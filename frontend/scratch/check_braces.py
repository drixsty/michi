def check_braces(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    stack = []
    pairs = {'{': '}', '(': ')', '[': ']', '<': '>'}
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        for char in line:
            if char in '{([<':
                stack.append((char, i+1))
            elif char in '})] >':
                if not stack:
                    # Ignore standalone > if not part of a tag (very rough)
                    if char == '>' and '&' not in line: 
                        continue
                    print(f"ERROR: Unmatched {char} at line {i+1}")
                    continue
                last_char, last_line = stack.pop()
                if pairs[last_char] != char:
                    if last_char == '<' and char == ' ': # Tag handle
                        stack.append((last_char, last_line))
                        continue
                    print(f"ERROR: Mismatched {last_char} (line {last_line}) with {char} (line {i+1})")
    
    for char, line in stack:
        print(f"ERROR: Unclosed {char} at line {line}")

if __name__ == "__main__":
    import sys
    check_braces(sys.argv[1])
