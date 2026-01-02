from flask import Blueprint, request, jsonify
from loguru import logger

from services.google_maps_service import GoogleMapsService
from services.place_mapping import PlaceMappingService
from services.gmap_screenshot_service import capture_route_screenshot_sync

from utils.log_sanitizer import sanitize_log_input
from utils.path_manager import get_temp_maps_dir, get_relative_path

from datetime import datetime
from pathlib import Path

bp = Blueprint("calculate", __name__)
maps_service = GoogleMapsService()
place_mapping = PlaceMappingService()


@bp.route("/distance", methods=["POST"])
def calculate_distance():
    """
    計算單筆距離
    """
    try:
        data = request.get_json() or {}
        origin = (data.get("origin") or "").strip()
        destination = (data.get("destination") or "").strip()

        if not origin or not destination:
            return jsonify({"status": "error", "message": "請提供起點和終點"}), 400

        origin_address = place_mapping.get_address(origin) or origin
        destination_address = place_mapping.get_address(destination) or destination

        route_detail = maps_service.get_route_detail(
            origin_address, destination_address, alternatives=True
        )

        if not route_detail.get("success"):
            return jsonify({
                "status": "error",
                "message": route_detail.get("error", "計算距離失敗")
            }), 400

        alternative_polylines = route_detail.get("alternative_polylines", [])
        map_image_path = maps_service.download_static_map_with_polyline(
            route_detail["polyline"],
            origin_address,
            destination_address,
            distance_km=route_detail["distance_km"],
            alternative_polylines=alternative_polylines,
        )

        response_data = {
            "status": "success",
            "data": {
                "one_way_km": route_detail["distance_km"],
                "round_trip_km": route_detail["round_trip_km"],
                "estimated_time": route_detail.get("estimated_time"),
                "estimated_seconds": route_detail.get("estimated_seconds"),
                "navigation_url": route_detail["map_url"],
                "map_image_path": map_image_path,
                "origin_address": origin_address,
                "destination_address": destination_address,
            },
        }

        safe_origin = sanitize_log_input(origin)
        safe_destination = sanitize_log_input(destination)
        logger.info(f"成功計算距離: {safe_origin} -> {safe_destination}, {route_detail['distance_km']} 公里")

        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"計算距離錯誤: {str(e)}")
        return jsonify({"status": "error", "message": f"計算距離失敗: {str(e)}"}), 500


@bp.route("/batch", methods=["POST"])
def calculate_batch():
    """
    批次計算多筆距離
    """
    try:
        data = request.get_json() or {}
        records = data.get("records", []) or []
        fixed_origin = (data.get("fixed_origin") or "").strip()

        if not records:
            return jsonify({"status": "error", "message": "沒有提供資料"}), 400

        updated_records = []
        errors = []

        for idx, record in enumerate(records):
            try:
                is_driving = (record.get("IsDriving", "N") or "N").upper()
                if is_driving != "Y":
                    updated_records.append(record)
                    continue

                origin_name = (record.get("起點名稱") or "").strip()
                destination_name = (record.get("目的地名稱") or "").strip()

                if not origin_name or not destination_name:
                    errors.append(f"第 {idx + 1} 筆資料缺少起點或終點")
                    updated_records.append(record)
                    continue

                # 起點
                if fixed_origin:
                    origin_address = fixed_origin
                else:
                    origin_geocode = maps_service.geocode(origin_name)
                    if origin_geocode:
                        origin_address = origin_geocode.get("formatted_address", origin_name)
                        logger.info(f"第 {idx + 1} 筆資料起點 Google Maps 解析成功: {origin_name} -> {origin_address}")
                    else:
                        mapped_origin = place_mapping.get_address(origin_name)
                        origin_address = mapped_origin if mapped_origin else origin_name
                        if mapped_origin:
                            logger.info(f"第 {idx + 1} 筆資料起點使用對應表: {origin_name} -> {origin_address}")
                        else:
                            logger.warning(f"第 {idx + 1} 筆資料起點無法解析，使用原始名稱: {origin_name}")

                # 終點
                destination_geocode = maps_service.geocode(destination_name)
                if destination_geocode:
                    destination_address = destination_geocode.get("formatted_address", destination_name)
                    logger.info(f"第 {idx + 1} 筆資料終點 Google Maps 解析成功: {destination_name} -> {destination_address}")
                else:
                    mapped_destination = place_mapping.get_address(destination_name)
                    destination_address = mapped_destination if mapped_destination else destination_name
                    if mapped_destination:
                        logger.info(f"第 {idx + 1} 筆資料終點使用對應表: {destination_name} -> {destination_address}")
                    else:
                        logger.warning(f"第 {idx + 1} 筆資料終點無法解析，使用原始名稱: {destination_name}")

                # 起終點檢查
                if origin_address == destination_address and origin_name == destination_name:
                    errors.append(f"第 {idx + 1} 筆資料起點和終點完全相同: {origin_name}")
                    logger.warning(f"第 {idx + 1} 筆資料起點和終點完全相同: {origin_name}")
                    updated_records.append(record)
                    continue
                elif origin_address == destination_address and origin_name != destination_name:
                    logger.info(f"第 {idx + 1} 筆資料對應地址相同，改用原始名稱計算: {origin_name} -> {destination_name}")
                    origin_address = origin_name
                    destination_address = destination_name

                safe_origin = sanitize_log_input(origin_address)
                safe_destination = sanitize_log_input(destination_address)
                logger.info(f"第 {idx + 1} 筆資料計算: {origin_name} ({safe_origin}) -> {destination_name} ({safe_destination})")

                route_detail = maps_service.get_route_detail(
                    origin_address, destination_address, alternatives=True
                )

                if not route_detail.get("success"):
                    error_msg = route_detail.get("error", "未知錯誤")
                    errors.append(f"第 {idx + 1} 筆資料計算失敗: {error_msg}")
                    logger.warning(f"第 {idx + 1} 筆資料計算失敗: {safe_origin} -> {safe_destination}, 錯誤: {error_msg}")
                    updated_records.append(record)
                    continue

                distance_km = route_detail.get("distance_km", 0) or 0
                if distance_km == 0:
                    errors.append(f"第 {idx + 1} 筆資料計算結果為 0 公里，請檢查地址是否正確: {origin_address} -> {destination_address}")
                    logger.warning(f"第 {idx + 1} 筆資料計算結果為 0 公里: {safe_origin} -> {safe_destination}")
                    updated_records.append(record)
                    continue

                # Playwright 截圖（完整路線頁）
                screenshot_path: Path | None = None
                try:
                    temp_maps_dir = get_temp_maps_dir()  # Path
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                    screenshot_filename = f"gmap_route_{timestamp}.png"
                    expected_path = temp_maps_dir / screenshot_filename

                    logger.info(f"開始使用 Playwright 截取 Google Maps 路線: {safe_origin} -> {safe_destination}")
                    screenshot_result = capture_route_screenshot_sync(
                        origin=origin_address,
                        destination=destination_address,
                        output_path=str(expected_path),
                        viewport_width=1500,
                        viewport_height=750,
                    )

                    if screenshot_result:
                        # 有些實作會回傳字串路徑
                        screenshot_path = Path(screenshot_result)
                    else:
                        screenshot_path = expected_path if expected_path.exists() else None

                    if screenshot_path and screenshot_path.exists():
                        logger.info(f"成功截取 Google Maps 路線截圖: {screenshot_path}")
                    else:
                        logger.warning("Playwright 截圖失敗，回退使用靜態地圖")
                        screenshot_path = None

                except Exception as e:
                    logger.warning(f"Playwright 截圖過程發生錯誤: {str(e)}，回退使用靜態地圖")
                    screenshot_path = None

                # 回退：Google Maps 官方樣式靜態地圖（含替代路線）
                if not screenshot_path:
                    logger.info("回退使用 Google Maps 官方樣式靜態地圖")
                    alternative_polylines = route_detail.get("alternative_polylines", [])
                    map_image_path = maps_service.download_static_map_with_polyline(
                        route_detail["polyline"],
                        origin_address,
                        destination_address,
                        distance_km=route_detail["distance_km"],
                        alternative_polylines=alternative_polylines,
                    )
                    if map_image_path:
                        screenshot_path = Path(map_image_path) if not isinstance(map_image_path, Path) else map_image_path

                # 更新紀錄
                record["OneWayKm"] = route_detail["distance_km"]
                record["RoundTripKm"] = route_detail["round_trip_km"]
                record["GoogleMapUrl"] = route_detail["map_url"]
                record["StepCount"] = route_detail.get("step_count")
                record["Polyline"] = route_detail.get("polyline")
                record["RouteSteps"] = route_detail.get("route_steps_text")

                record["OriginAddress"] = origin_address
                record["DestinationAddress"] = destination_address

                if "estimated_time" in route_detail:
                    record["EstimatedTime"] = route_detail.get("estimated_time")

                if screenshot_path and screenshot_path.exists():
                    record["StaticMapImage"] = get_relative_path(str(screenshot_path))
                else:
                    record["StaticMapImage"] = None

                updated_records.append(record)

            except Exception as e:
                logger.error(f"處理第 {idx + 1} 筆資料錯誤: {str(e)}")
                errors.append(f"第 {idx + 1} 筆資料處理失敗: {str(e)}")
                updated_records.append(record)

        calculated_count = sum(
            1 for r in updated_records
            if ("OneWayKm" in r) and (r.get("OneWayKm") is not None)
        )

        response_data = {
            "status": "success",
            "data": {
                "records": updated_records,
                "total_count": len(updated_records),
                "calculated_count": calculated_count,
                "errors": errors,
            },
            "message": f"部分資料計算失敗: {len(errors)} 筆" if errors else f"成功計算 {calculated_count} 筆資料",
        }

        logger.info(f"批次計算完成: {len(updated_records)} 筆, 成功 {calculated_count} 筆")
        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"批次計算錯誤: {str(e)}")
        return jsonify({"status": "error", "message": f"批次計算失敗: {str(e)}"}), 500
