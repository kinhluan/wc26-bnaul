import sys

with open("src/wc26_bnaul/auto_agent.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update argparse
old_argparse = '''    parser.add_argument("--ask-agent", action="store_true", help="Ask agent (interactive mode)")
    parser.add_argument("--ask-kimi", action="store_true", help=argparse.SUPPRESS)  # deprecated alias, still works'''

new_argparse = '''    parser.add_argument("--ask-agent", action="store_true", help="Ask agent (interactive mode)")
    parser.add_argument("--ask-kimi", action="store_true", help="Manual copy-paste mode: ask Kimi in browser and paste response back")'''
content = content.replace(old_argparse, new_argparse)

# 2. Fix cli_mode logic
old_cli = '''    cli_mode = args.cli_mode or args.ask_agent or getattr(args, "ask_kimi", False)'''
new_cli = '''    cli_mode = args.cli_mode'''
content = content.replace(old_cli, new_cli)
content = content.replace('''    cli_mode = args.cli_mode or args.ask_agent\n''', '''    cli_mode = args.cli_mode\n''')

# 3. Fix prompts
old_prompt1 = '''prompt = f"""You are a football match prediction expert with access to real-time web search.

TASK: Analyze the following match data and provide a PROBABILITY ADJUSTMENT for the home team's win probability.'''

new_prompt1 = '''prompt = f"""You are a Math PhD in statistical sports analysis and an expert football commentator with access to real-time web search.

TASK: Analyze the following match data mathematically and intuitively to provide a PROBABILITY ADJUSTMENT for the home team's win probability.'''
content = content.replace(old_prompt1, new_prompt1)

old_prompt2 = '''{"role": "system", "content": "You are a football prediction assistant."},'''
new_prompt2 = '''{"role": "system", "content": "You are a Math PhD specializing in statistical sports modeling and a veteran football commentator. Your tone is highly analytical, mathematically rigorous, yet engaging like a sports pundit."},'''
content = content.replace(old_prompt2, new_prompt2)

# 4. Insert ask-kimi logic at the very beginning of call_llm_api
ask_kimi_block = '''    # 1. Copy-Paste manual (ask-kimi) mode
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
            except EOFError:
                return 0.0
            except Exception:
                pass
            
            # parse
            import re
            
            # try to find ADJUSTMENT: -X.X
            adj_match = re.search(r'ADJUSTMENT:\s*([+-]?\d+(?:\.\d+)?)', raw_input, flags=re.IGNORECASE)
            adjustment = float(adj_match.group(1)) if adj_match else 0.0
            
            reasoning = "Không có lời giải thích cụ thể."
            parts = re.split(r'ADJUSTMENT:\s*[+-]?\d+(?:\.\d+)?%?', raw_input, flags=re.IGNORECASE)
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
                except EOFError:
                    return adjustment
'''

# We need to remove the existing ask-kimi block from the try-except block, then insert the new one before cli_mode.
# First, find and remove the old ask-kimi block (starts with "Nếu có cờ --ask-agent" and ends with "override_adj")
old_ask_kimi_start = content.find("        # Nếu có cờ --ask-agent")
if old_ask_kimi_start != -1:
    old_ask_kimi_end = content.find("return 0.0", old_ask_kimi_start) + 10
    # Wait, the second return 0.0 is at KeyboardInterrupt. Let's just find the end of the while loop.
    old_ask_kimi_end = content.find("        # Nếu có API Key", old_ask_kimi_start)
    if old_ask_kimi_end != -1:
        content = content[:old_ask_kimi_start] + content[old_ask_kimi_end:]

# Now insert the new ask_kimi_block before "if cli_mode:"
cli_mode_idx = content.find("    if cli_mode:")
if cli_mode_idx != -1:
    content = content[:cli_mode_idx] + ask_kimi_block + "\n" + content[cli_mode_idx:]

with open("src/wc26_bnaul/auto_agent.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied successfully.")
