import sys

with open("src/wc26_bnaul/auto_agent.py", "r", encoding="utf-8") as f:
    content = f.read()

# Remove the --ask-kimi block from the try-except block
start_str = """        # Nếu có cờ --ask-agent (hoặc --ask-kimi cũ), dùng cơ chế Copy-Paste thủ công (Human-in-the-loop)
        if "--ask-agent" in sys.argv or "--ask-kimi" in sys.argv:"""

end_str = """                        print("\\n[ASK AGENT] Interrupted. Returning 0.0")
                        return 0.0"""

start_idx = content.find(start_str)
end_idx = content.find(end_str, start_idx) + len(end_str)

if start_idx == -1:
    print("Could not find start block")
    sys.exit(1)

ask_kimi_block = content[start_idx:end_idx]
# Adjust indentation of ask_kimi_block
lines = ask_kimi_block.split("\n")
new_lines = []
for line in lines:
    if line.startswith("        "):
        new_lines.append(line[4:])
    else:
        new_lines.append(line)
ask_kimi_block = "\n".join(new_lines)
ask_kimi_block = ask_kimi_block.replace("# Nếu có cờ", "# 1. Chế độ Copy-Paste thủ công")

content = content[:start_idx] + content[end_idx:]

# Insert it before `if cli_mode:`
insert_str = "    if cli_mode:"
insert_idx = content.find(insert_str)
content = content[:insert_idx] + ask_kimi_block + "\n\n" + content[insert_idx:]

with open("src/wc26_bnaul/auto_agent.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Done replacing.")
