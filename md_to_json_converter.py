import os
import re
import json
from pathlib import Path

def parse_star_difficulty(line):
    """解析星號難度，回傳星號字串和對應的文字描述"""
    stars = line.strip().count('★')
    star_map = {1: "★", 2: "★★", 3: "★★★", 4: "★★★★", 5: "★★★★★"}
    text_map = {1: "1顆星 (簡單)", 2: "2顆星 (稍有難度)", 3: "3顆星 (中等)", 4: "4顆星 (挑戰)", 5: "5顆星 (大師級)"}
    return star_map.get(stars, ""), text_map.get(stars, "未知難度")

def sanitize_foldername(name):
    """
    將食譜名稱轉換為適合做資料夾名稱的字串。
    移除 "的做法", "食譜" 等後綴，並將非法字元替換為底線。
    """
    name = name.replace("的做法", "")
    name = name.replace("食譜", "")
    name = name.strip()
    # 移除非法字元，並將空格替換為底線
    # 這裡的非法字元列表可能需要根據您的作業系統和需求調整
    # Windows 不允許的字元: < > : " / \ | ? *
    # Linux/macOS 不允許 /
    name = re.sub(r'[<>:"/\\|?*\s]+', '_', name)
    # 移除可能的多餘底線
    name = re.sub(r'_+', '_', name)
    name = name.strip('_') # 移除首尾可能產生的底線
    return name if name else "unknown_recipe" # 避免空資料夾名

def parse_md_recipe(md_content, filename):
    """解析單個 Markdown 食譜內容，加入音訊路徑生成，副檔名為 .wav"""
    recipe_data = {
        "recipe_name": Path(filename).stem, # 初始食譜名，之後可能會被 H1 覆蓋或處理
        "source_file": filename,
        "difficulty_stars": "",
        "difficulty_text": "",
        "moods": [],
        "categories": [],
        "required_items_text": "",
        "calculations_text": "",
        "steps": [],
        "notes_text": "",
        "description_for_recommendation": ""
    }
    
    lines = md_content.splitlines()
    current_section_title = None
    current_section_content = []

    # 嘗試從第一行 H1 獲取食譜名稱並優先使用
    if lines and lines[0].startswith("# "):
        recipe_data["recipe_name"] = lines[0][2:].strip()
        lines = lines[1:] # 移除已處理的 H1
    
    # 根據最終的 recipe_name 生成用於音訊路徑的資料夾名
    # 這個 recipe_name 是 Markdown 中解析出的主要名稱
    clean_recipe_name_for_folder = sanitize_foldername(recipe_data["recipe_name"])

    def process_previous_section_content():
        nonlocal current_section_title, current_section_content, clean_recipe_name_for_folder
        if current_section_title and current_section_content:
            content_str = "\n".join(current_section_content).strip()
            if current_section_title == "預估烹飪難度：":
                if current_section_content:
                    stars_str, text_str = parse_star_difficulty(current_section_content[0])
                    recipe_data["difficulty_stars"] = stars_str
                    recipe_data["difficulty_text"] = text_str
            elif current_section_title == "心情：":
                recipe_data["moods"] = [item[2:].strip() for item in current_section_content if item.startswith("- ")]
            elif current_section_title == "類別":
                recipe_data["categories"] = [item[2:].strip() for item in current_section_content if item.startswith("- ")]
            elif current_section_title == "必備原料和工具":
                recipe_data["required_items_text"] = content_str
            elif current_section_title == "計算":
                recipe_data["calculations_text"] = content_str
            elif current_section_title == "操作":
                step_order = 1
                for item_line in current_section_content:
                    if re.match(r"^\d+\.\s+", item_line):
                        instruction = re.sub(r"^\d+\.\s+", "", item_line).strip()
                        # --- 生成音訊路徑 (副檔名改為 .wav) ---
                        audio_base_path = f"assets/audio/recipe_steps/{clean_recipe_name_for_folder}"
                        audio_mandarin_path = f"{audio_base_path}/step_{step_order}_mandarin.wav" # <--- 副檔名修改
                        audio_taiwanese_path = f"{audio_base_path}/step_{step_order}_taiwanese.wav" # <--- 副檔名修改
                        animation_cue = f"cue_step_{step_order}" 
                        # --- 結束生成 ---
                        recipe_data["steps"].append({
                            "order": step_order,
                            "instruction": instruction,
                            "audioPathMandarin": audio_mandarin_path,
                            "audioPathTaiwanese": audio_taiwanese_path,
                            "animationCue": animation_cue
                        })
                        step_order += 1
            elif current_section_title == "附加內容":
                recipe_data["notes_text"] = content_str
        current_section_content = []

    for line_raw in lines:
        line = line_raw.strip()
        if line.startswith("## "):
            process_previous_section_content()
            current_section_title = line[3:].strip()
        elif current_section_title and line_raw.strip():
            if line_raw.strip() != "---":
                current_section_content.append(line_raw.strip())
        elif not current_section_title and line_raw.strip() and line_raw.strip() != "---" and not line_raw.startswith("# "):
            pass

    process_previous_section_content()

    # 組合推薦描述
    difficulty_display = recipe_data["difficulty_stars"]
    mood_display = recipe_data["moods"][0] if recipe_data["moods"] else ""
    category_display = recipe_data["categories"][0] if recipe_data["categories"] else ""
    desc_parts = []
    if difficulty_display: desc_parts.append(difficulty_display)
    if mood_display: desc_parts.append(mood_display)
    if category_display: desc_parts.append(category_display)
    recipe_data["description_for_recommendation"] = " - ".join(filter(None, desc_parts))
    if not recipe_data["description_for_recommendation"] and recipe_data["steps"]:
        recipe_data["description_for_recommendation"] = recipe_data["steps"][0]["instruction"][:30] + "..."
    elif not recipe_data["description_for_recommendation"]:
         recipe_data["description_for_recommendation"] = "美味料理，等你來試！"
    
    # 統一 recipe_name (移除 "的做法" 等，與 sanitize_foldername 的邏輯應保持一致或呼叫它)
    # 確保 recipe_data["recipe_name"] 也是處理過的純菜名，以便 Flutter 端 image_mappings.dart 的 key 能對上
    recipe_data["recipe_name"] = sanitize_foldername(recipe_data["recipe_name"])


    return recipe_data

def batch_convert_md_to_json(input_folder, output_folder):
    """批次轉換資料夾中的 MD 檔案到 JSON"""
    input_path = Path(input_folder)
    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    all_recipes_data = []

    for md_file in input_path.glob("*.md"):
        print(f"正在處理: {md_file.name}")
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            recipe_json = parse_md_recipe(content, md_file.name)
            all_recipes_data.append(recipe_json)
        except Exception as e:
            print(f"處理檔案 {md_file.name} 時發生錯誤: {e}")
    
    all_recipes_output_path = output_path / "all_recipes.json"
    with open(all_recipes_output_path, "w", encoding="utf-8") as f_all_out:
        json.dump(all_recipes_data, f_all_out, ensure_ascii=False, indent=4)
    print(f"\n所有食譜數據已儲存到: {all_recipes_output_path}")


if __name__ == "__main__":
    input_directory = "dishes" 
    output_directory = "output_json_with_wav_audio_paths" # 更新輸出資料夾名以示區別

    if not Path(input_directory).is_dir():
        print(f"錯誤：輸入資料夾 '{input_directory}' 不存在或不是一個目錄。請將您的 MD 檔案放入此資料夾。")
    else:
        batch_convert_md_to_json(input_directory, output_directory)