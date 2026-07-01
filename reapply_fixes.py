import sys

with open("src/wc26_bnaul/auto_agent.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add --ask-kimi to argparse
content = content.replace(
    'parser.add_argument("--interactive", action="store_true", help="Interactive mode: get LLM advice and ask for user confirmation before submitting")',
    'parser.add_argument("--interactive", action="store_true", help="Interactive mode: get LLM advice and ask for user confirmation before submitting")\n    parser.add_argument("--ask-kimi", action="store_true", help="Manual copy-paste mode: ask Kimi in browser and paste response back")'
)

# Fix line 1345 cli_mode
content = content.replace(
    'cli_mode = args.cli_mode or args.ask_agent or getattr(args, "ask_kimi", False)',
    'cli_mode = args.cli_mode'
)
content = content.replace(
    'cli_mode = args.cli_mode or args.ask_agent',
    'cli_mode = args.cli_mode'
)

# 2. Update prompt
content = content.replace(
    'You are a football prediction assistant.',
    'You are a Math PhD specializing in statistical sports modeling and a veteran football commentator. Your tone is highly analytical, mathematically rigorous, yet engaging like a sports pundit.'
)

content = content.replace(
    'You are a football match prediction expert with access to real-time web search.',
    'You are a Math PhD in statistical sports analysis and an expert football commentator with access to real-time web search.'
)

content = content.replace(
    'TASK: Analyze the following match data and provide a PROBABILITY ADJUSTMENT for the home team\'s win probability.',
    'TASK: Analyze the following match data mathematically and intuitively to provide a PROBABILITY ADJUSTMENT for the home team\'s win probability.'
)

# 3. Rewrite call_llm_api completely up to the Real API Call mode
import re
new_call_llm_api = '''def call_llm_api(prompt: str, dry_run: bool = False, cli_mode: bool = False) -> float:
    import sys
    import os
    import re
    
    # 1. Copy-Paste manual (ask-kimi) mode
    if "--ask-agent" in sys.argv or "--ask-kimi" in sys.argv:
        print(f"\\n{'='*60}")
        print(f"🤖 LLM PROMPT (Hãy copy nội dung dưới đây dán vào ChatGPT/Kimi/Claude):")
        print(f"{'='*60}")
        print(prompt)
        print(f"{'='*60}")
        
        while True:
            print("\\n📝 Dán câu trả lời của AI vào đây (Nhấn Ctrl+D / Ctrl+Z ở dòng mới khi dán xong):")
            try:
                raw_input = sys.stdin.read()
                try:
                    sys.stdin = open('/dev/tty')
                except OSError:
                    pass
            except KeyboardInterrupt:
                print("\\n[ASK AGENT] Interrupted. Returning 0.0")
                return 0.0
            except Exception:
                pass
            
            adjustment = _parse_adjustment_from_text(raw_input)
            
            reasoning = "Không có lời giải thích cụ thể."
            parts = re.split(r'ADJUSTMENT:\\s*[+-]?\\d+(?:\\.\\d+)?%?', raw_input, flags=re.IGNORECASE)
            if len(parts) > 1 and parts[-1].strip():
                clean_reasoning = parts[-1].strip().replace('\\n', ' ').strip()
                reasoning = clean_reasoning[:200] + ("..." if len(clean_reasoning) > 200 else "")
            
            print(f"\\n{'='*60}")
            print(f"🤖 [KIMI TƯ VẤN - QUA BẢN TEXT BẠN PASTE]")
            print(f"💡 Nhận định: {reasoning}")
            print(f"🎯 Chốt số: Điều chỉnh {adjustment:+.1f}%")
            print(f"{'='*60}")
            
            while True:
                try:
                    val = input(f"👉 Bạn có chốt con số {adjustment:+.1f}% này không? [Nhập số khác để Override / Nhấn Enter để Đồng ý]: ").strip()
                    if not val:
                        print(f"✅ Đã chốt: {adjustment:+.1f}%")
                        return adjustment
                    override_adj = float(val.replace("%", ""))
                    print(f"✅ Đã ghi đè thành: {override_adj:+.1f}%")
                    return override_adj
                except ValueError:
                    print("❌ Lỗi: Vui lòng nhập một số hợp lệ (ví dụ: -2.5 hoặc 1.0)")
                except KeyboardInterrupt:
                    print("\\n[ASK AGENT] Interrupted. Returning 0.0")
                    return 0.0

    # 2. CLI mode
    if cli_mode:
        print(f"\\n{'='*60}")
        print("LLM PROMPT (cli_mode — output for external CLI agent):")
        print(f"{'='*60}")
        print(prompt)
        print(f"{'='*60}")
        print("\\n[CLI MODE] Waiting for ADJUSTMENT from stdin...")
        print("Format: ADJUSTMENT: [value]  (e.g., ADJUSTMENT: -2.5)")
        print("Enter adjustment and press Ctrl+D (Unix) or Ctrl+Z (Windows) when done:")
        print("-" * 60)

        try:
            raw_input = sys.stdin.read()
        except KeyboardInterrupt:
            print("\\n[CLI MODE] Interrupted. Returning 0.0")
            return 0.0

        adjustment = _parse_adjustment_from_text(raw_input)
        print(f"[CLI MODE] Parsed adjustment: {adjustment:+.1f}%")
        return adjustment

    # 3. Dry run
    if dry_run:
        print(f"\\n{'='*60}")
        print("LLM PROMPT (dry_run — would send to API):")
        print(f"{'='*60}")
        preview = prompt[:500] + "..." if len(prompt) > 500 else prompt
        print(preview)
        print(f"\\n[DRY RUN] Would call LLM API. Returning default adjustment: 0.0")
        return 0.0

    # 4. Real API call
    try:
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("KIMI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "[LLM API] CRITICAL ERROR: No API key found and --ask-kimi not used.\\n"
                "To use manual copy-paste mode, run with --ask-kimi flag.\\n"
                "To use auto mode, set OPENAI_API_KEY or KIMI_API_KEY in .env"
            )
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.moonshot.cn/v1" if "KIMI" in os.environ else None)
        
        print("\\n⏳ Đang kết nối API lấy tư vấn từ AI Agent...")
        response = client.chat.completions.create(
            model="moonshot-v1-8k" if "KIMI" in os.environ else "gpt-4o",
            messages=[
                {"role": "system", "content": "You are a Math PhD specializing in statistical sports modeling and a veteran football commentator. Your tone is highly analytical, mathematically rigorous, yet engaging like a sports pundit."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        llm_response = response.choices[0].message.content
        adjustment = _parse_adjustment_from_text(llm_response)
        
        reasoning = "Không có lời giải thích cụ thể."
        parts = re.split(r'ADJUSTMENT:\\s*[+-]?\\d+(?:\\.\\d+)?%?', llm_response, flags=re.IGNORECASE)
        if len(parts) > 1 and parts[-1].strip():
            clean_reasoning = parts[-1].strip().replace('\\n', ' ').strip()
            reasoning = clean_reasoning[:200] + ("..." if len(clean_reasoning) > 200 else "")
            
        print(f"\\n{'='*60}")
        print(f"🤖 [AI TƯ VẤN TỰ ĐỘNG]")
        print(f"💡 Nhận định: {reasoning}")
        print(f"🎯 Chốt số: Điều chỉnh {adjustment:+.1f}%")
        print(f"{'='*60}")
        
        if "--interactive" in sys.argv:
            while True:
                try:
                    val = input(f"\\n👉 Bạn có đồng ý với số {adjustment:+.1f}% không? [Nhập số khác để Override / Nhấn Enter để Đồng ý]: ").strip()
                    if not val:
                        return adjustment
                    override_adj = float(val.replace("%", ""))
                    print(f"✅ Đã ghi đè thành: {override_adj:+.1f}%")
                    return override_adj
                except ValueError:
                    print("❌ Lỗi: Vui lòng nhập một số hợp lệ (ví dụ: -2.5 hoặc 1.0)")
                except KeyboardInterrupt:
                    print("\\n[INTERACTIVE] Interrupted. Returning 0.0")
                    return 0.0
                    
        return adjustment
    except ImportError:
        print("\\n[LLM API] openai library not found. Please run: pip install openai")
        return 0.0'''

# Find the start of def call_llm_api and end of the try-except block
start_idx = content.find("def call_llm_api(")
end_str = "        return 0.0"
end_idx = content.find(end_str, content.find("except ImportError:", start_idx)) + len(end_str)

content = content[:start_idx] + new_call_llm_api + content[end_idx:]

with open("src/wc26_bnaul/auto_agent.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Done reapplying fixes.")
