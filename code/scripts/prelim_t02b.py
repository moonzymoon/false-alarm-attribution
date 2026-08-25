"""预跑: 用已交回的 4 份学生标签先出初步结果 (正式数字等全部标注到齐后重跑)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import run_t02b as T  # noqa: E402

T.PKG = r"D:\0科研\工作1\第10篇SCI\04_投稿准备\T0_投稿前实验包\学生标注结果"
T.analyze()
