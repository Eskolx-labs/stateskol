import importlib.util, pathlib
p = pathlib.Path(__file__).resolve().parents[1] / "src" / "stateskol" / "welford (Maria).py"
s = importlib.util.spec_from_file_location("w", p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
print(m.welford([2, 4, 4, 4, 5, 5, 7, 9, None]))
