import re, time
from pathlib import Path
from src.interface_extractor import mask_comments

raw = Path('case_studies/nav2/nav2_behavior_tree/include/nav2_behavior_tree/utils/test_action_server.hpp').read_text(encoding='utf-8')
clean = mask_comments(raw)
print('Length of clean:', len(clean))

pat = re.compile(r'\b(?:create_action_server|create_server|SimpleActionServer)\s*<\s*([^>]+)\s*>\s*\(([^;)]+)\)', re.DOTALL)
t0 = time.time()
for m in pat.finditer(clean):
    raw_type = m.group(1).strip()
    args = m.group(2)
    name_m = re.search(r'"([^"]+)"', args)
    name = name_m.group(1) if name_m else "unnamed"
    print(f'Match: type={raw_type}, name={name}')
print(f'Finished in {time.time()-t0:.3f}s')

