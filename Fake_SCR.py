import os
import sys
# 假ScreenRender.exe

# 保存路径：优先从命令行参数读取，否则使用环境变量，最后回退默认
MLsavepath = ""
for arg in sys.argv:
    if arg.startswith("--savepath="):
        MLsavepath = arg.split("=", 1)[1]
        break
if not MLsavepath:
    MLsavepath = os.environ.get("OSEASY_SCR_SAVEPATH") or os.path.join(os.getcwd(), "SCCMD.txt")

emp = []
for i in sys.argv:
    emp.append(str(i))

for data in emp:
    repcmd = data.replace("#fullscreen#:1", "#fullscreen#:0").replace(" ", "")

fm = open(MLsavepath, "w")
fm.write(str(repcmd))
fm.close()
print("拦截命令成功 你可以暴力脱离控制")
print("并使用广播管理页的功能了")