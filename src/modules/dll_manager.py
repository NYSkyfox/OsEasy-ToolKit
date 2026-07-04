# src/modules/dll_manager.py
# DLL 加载与调用

import ctypes


class easy_dll:
    def __init__(self, dll_path):
        self.dll = ctypes.WinDLL(dll_path)

    def setup_function(self, func_name, restype=ctypes.c_int, argtypes=None):
        """
        Configures a DLL function with the specified name, return type, and argument types.

        :param func_name: Name of the function in the DLL.
        :param restype: Return type of the function (default is c_int).
        :param argtypes: List of argument types (default is None).
        """
        func = getattr(self.dll, func_name)
        func.restype = restype
        func.argtypes = argtypes or []
        return func

    def get_error_message(self, error_code):
        """
        Helper function to retrieve Windows error message for a given error code.

        :param error_code: Error code to look up.
        :return: The formatted error message string.
        """
        msg_buffer = ctypes.create_unicode_buffer(256)
        ctypes.windll.kernel32.FormatMessageW(
            0x00001000,  # FORMAT_MESSAGE_FROM_SYSTEM
            None,
            error_code,
            0,  # Default language
            msg_buffer,
            len(msg_buffer),
            None,
        )
        return msg_buffer.value


def run_easy_dll(
    dll_name, func_name, return_type, argtypes, out_buffer, after_run_func=None
):
    """
    ### 参数
    - `dll_name`: 要调用的dll文件名
    - `func_name`: 要调用的函数名
    - `return_type`: 要调用的函数的返回值类型
    - `argtypes`: 要调用的函数的参数类型
    - `out_buffer`: 要调用的函数的输出参数
    - `after_run_func`: 运行完毕后的回调函数

    """
    from src.core.runtime_config import toolbox_cfg
    from src.core.helpers import Ui_call_show_snake_message

    print("dllUse debug >", dll_name, func_name, return_type, argtypes, out_buffer)

    dll_path = toolbox_cfg.oseasy_path + dll_name

    easy_dll = easy_dll(dll_path)

    runner = easy_dll.setup_function(func_name, restype=return_type, argtypes=argtypes)

    try:
        if out_buffer == None:
            result = runner()
        else:
            result = runner(out_buffer)
    except Exception as e:
        Ui_call_show_snake_message(f"调用失败 抛出异常：\n{e}")

    print("[DEBUG] dll result:", result)

    ui_show_msg = f"运行结果: \n函数: {func_name}\n返回值: {result}"
    if out_buffer != None:
        ui_show_msg += f"\n输出参数: {out_buffer.value}"

    if result != 0:
        error_msg = easy_dll.get_error_message(result)
        print("[DEBUG] Error message:", error_msg)
        ui_show_msg += f"\n错误信息: {error_msg}"

    Ui_call_show_snake_message(ui_show_msg)

    if after_run_func != None:
        after_run_func()