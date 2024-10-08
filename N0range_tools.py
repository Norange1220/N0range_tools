import tkinter as tk
from tkinter import ttk, simpledialog
import requests
import subprocess
import json
import os
import importlib.util
import shutil
import threading
import asyncio

class PenetrationTestTool:
    def __init__(self, master):
        self.master = master
        self.master.title("N0range_tools")
        

        self.categories = []
        self.custom_tools = {}
        self.plugins = []
        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill="both")
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text="主页")

        self.plugins_frame = ttk.Frame(self.main_frame)
        self.plugins_frame.pack(side="top", fill="both", expand=True)

        self.management_frame = ttk.Frame(self.main_frame)
        self.management_frame.pack(side="bottom", fill="x")

        self.buttons_frame = ttk.Frame(self.management_frame)
        self.buttons_frame.pack(expand=True)

        self.manage_categories_button = tk.Button(self.buttons_frame, text="管理分类", command=self.manage_categories)
        self.manage_categories_button.pack(side="left", padx=5, pady=5)

        self.manage_tools_button = tk.Button(self.buttons_frame, text="管理工具", command=self.manage_tools)
        self.manage_tools_button.pack(side="left", padx=5, pady=5)

        self.manage_plugins_button = tk.Button(self.buttons_frame, text="管理插件", command=self.manage_plugins)
        self.manage_plugins_button.pack(side="left", padx=5, pady=5)

        self.management_frame.pack_configure(expand=True)
        self.buttons_frame.pack_configure(expand=True)

        self.load_custom_tools()

        self.create_tool_categories()

        self.master.after(100, self.load_plugins)


    def load_custom_tools(self):
        if os.path.exists('custom_tools.json'):
            with open('custom_tools.json', 'r') as f:
                loaded_data = json.load(f)
                self.custom_tools = loaded_data
                self.categories = list(loaded_data.keys())
        else:
            self.custom_tools = {}
            self.categories = []

    def save_custom_tools(self):
        with open('custom_tools.json', 'w') as f:
            json.dump(self.custom_tools, f)

    def create_tool_categories(self):
        for category in self.categories:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=category)
            self.create_tool_buttons(frame, category)

    def create_tool_buttons(self, frame, category):
        main_frame = ttk.Frame(frame)
        main_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        row = 0
        col = 0
        tools = self.custom_tools.get(category, [])

        for tool in tools:
            btn = tk.Button(scrollable_frame, text=tool["name"], command=lambda t=tool: self.open_tool(t, category), width=12)  # 设置固定宽度为15
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")  
            col += 1
            if col > 4:  # 每行最多显示5个按钮
                col = 0
                row += 1

        for i in range(5):
            scrollable_frame.columnconfigure(i, weight=1)
        for i in range(row + 1):  
            scrollable_frame.rowconfigure(i, weight=1)

        scrollable_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(side="bottom", fill="x")

        add_btn = tk.Button(button_frame, text="添加工具", command=lambda c=category: self.add_custom_tool(c))
        add_btn.pack(pady=10)

    def add_custom_tool(self, category):
        tool_name = simpledialog.askstring("添加工具", f"请输入要添加到 {category} 的工具名称：")
        if tool_name:
            tool_path = self.ask_path(f"请输入 {tool_name} 的路径：")
            if tool_path:
                open_method, param_option, new_window_option = self.choose_open_method()
                if open_method and param_option and new_window_option is not None:
                    default_params = ""
                    fixed_params = ""
                    if param_option == "默认添加参数":
                        default_params = simpledialog.askstring("默认参数", "请输入默认参数：")
                    elif param_option == "固定参数+目标":
                        fixed_params = simpledialog.askstring("固定参数", "请输入固定参数：")
                    if category not in self.custom_tools:
                        self.custom_tools[category] = []
                    self.custom_tools[category].append({
                        "name": tool_name,
                        "path": tool_path,
                        "open_method": open_method,
                        "param_option": param_option,
                        "default_params": default_params,
                        "fixed_params": fixed_params,
                        "new_window": new_window_option
                    })
                    self.save_custom_tools()
                    self.rebuild_categories()

    def ask_path(self, prompt):
        dialog = tk.Toplevel(self.master)
        dialog.title("输入路径")
        dialog.geometry("400x100")  # 设置对话框大小

        tk.Label(dialog, text=prompt).pack(pady=5)
        entry = tk.Entry(dialog, width=50)  # 增加输入框宽度
        entry.pack(pady=5)

        path = [None]  

        def on_ok():
            path[0] = entry.get()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        tk.Button(dialog, text="确定", command=on_ok).pack(side=tk.LEFT, padx=10)
        tk.Button(dialog, text="取消", command=on_cancel).pack(side=tk.RIGHT, padx=10)

        dialog.transient(self.master)
        dialog.grab_set()
        self.master.wait_window(dialog)

        return path[0]

    def choose_open_method(self):
        methods = ["正常打开", "Python打开", "Java打开", "浏览器打开"]
        choice = simpledialog.askstring(
            "选择打开方式",
            "请选择打开程序的方式：\n1. 正常打开\n2. Python打开\n3. Java打开\n4. 浏览器打开\n请输入对应的数字："
        )
        if choice and choice.isdigit() and 1 <= int(choice) <= 4:
            method = methods[int(choice) - 1]
            param_option = self.choose_parameter_option()
            new_window_option = self.choose_new_window_option()
            return method, param_option, new_window_option
        else:
            tk.messagebox.showerror("错误", "无效的选择，请重试。")
            return None, None, None

    def choose_parameter_option(self):
        options = ["默认不添加参数", "默认添加参数", "每次打开都输入参数", "固定参数+目标"]
        choice = simpledialog.askstring(
            "选择参数选项",
            "请选择参数选项：\n1. 默认不添加参数\n2. 默认添加参数\n3. 每次打开都输入参数\n4. 固定参数+目标\n请输入对应的数字："
        )
        if choice and choice.isdigit() and 1 <= int(choice) <= 4:
            return options[int(choice) - 1]
        else:
            tk.messagebox.showerror("错误", "无效的选择，请重试。")
            return None

    def choose_new_window_option(self):
        choice = simpledialog.askstring(
            "选择新窗口选项",
            "是否每次都新打开窗口：\n1. 是\n2. 否\n请输入对应的数字："
        )
        if choice == "1":
            return True
        elif choice == "2":
            return False
        else:
            tk.messagebox.showerror("错误", "无效的选择，请重试。")
            return None

    def open_tool(self, tool, category):
        path = tool["path"]
        open_method = tool["open_method"]
        param_option = tool["param_option"]
        default_params = tool.get("default_params", "")
        fixed_params = tool.get("fixed_params", "")
        new_window = tool.get("new_window", False)

        params = ""
        if param_option == "每次打开都输入参数":
            params = simpledialog.askstring("输入参数", "请输入运行参数：", initialvalue=default_params)
        elif param_option == "默认添加参数":
            params = default_params
        elif param_option == "固定参数+目标":
            target = simpledialog.askstring("输入目标", "请输入目标：")
            params = f"{fixed_params} {target}" if target else fixed_params

        try:
            if open_method == "正常打开":
                if new_window:
                    if os.name == 'nt':  # Windows
                        subprocess.Popen(f"start cmd /k {path} {params}", shell=True)
                    else:  # Unix-like systems
                        subprocess.Popen(f"xterm -e '{path} {params}; read -p \"Press Enter to exit...\"'", shell=True)
                else:
                    subprocess.Popen(f"{path} {params}", shell=True)
            elif open_method == "Python打开":
                command = f"python {path} {params}"
                if new_window:
                    if os.name == 'nt':  # Windows
                        subprocess.Popen(f"start cmd /k {command} && pause", shell=True)
                    else:  # Unix-like systems
                        subprocess.Popen(f"xterm -e '{command}; read -p \"Press Enter to exit...\"'", shell=True)
                else:
                    subprocess.Popen(command, shell=True)
            elif open_method == "Java打开":
                if new_window:
                    if os.name == 'nt':  # Windows
                        subprocess.Popen(f"start cmd /k java -jar {path} {params} && pause", shell=True)
                    else:  # Unix-like systems
                        subprocess.Popen(f"xterm -e 'java -jar {path} {params}; read -p \"Press Enter to exit...\"'", shell=True)
                else:
                    subprocess.Popen(["java", "-jar", path] + params.split())
            elif open_method == "浏览器打开":
                import webbrowser
                browser = webbrowser.get()
                browser.open(f"{path}{params}", new=new_window)
            print(f"正在使用 {open_method} 方式打开工具：{tool['name']}，参数：{params}，新窗口：{new_window}")
        except Exception as e:
            tk.messagebox.showerror("错误", f"无法打开工具 {tool['name']}：{str(e)}")

    def manage_categories(self):
        manage_window = tk.Toplevel(self.master)
        manage_window.title("管理分类")
        manage_window.geometry("400x300")  # 设置窗口大小

        notebook = ttk.Notebook(manage_window)
        notebook.pack(expand=True, fill="both", padx=5, pady=5)

        existing_frame = ttk.Frame(notebook)
        notebook.add(existing_frame, text="现有分类")

        canvas = tk.Canvas(existing_frame)
        scrollbar = ttk.Scrollbar(existing_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for category in self.categories:
            frame = ttk.Frame(scrollable_frame)
            frame.pack(fill="x", padx=5, pady=2)

            label = tk.Label(frame, text=category)
            label.pack(side="left")

            rename_button = tk.Button(frame, text="重命名", command=lambda c=category: self.rename_category(c))
            rename_button.pack(side="right")

            delete_button = tk.Button(frame, text="删除", command=lambda c=category: self.delete_category(c))
            delete_button.pack(side="right", padx=5)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 添加新分类标签页
        add_frame = ttk.Frame(notebook)
        notebook.add(add_frame, text="添加新分类")

        new_category_label = tk.Label(add_frame, text="新分类名称:")
        new_category_label.pack(pady=(20, 5))

        new_category_entry = tk.Entry(add_frame, width=30)
        new_category_entry.pack(pady=5)

        add_button = tk.Button(add_frame, text="添加分类", command=lambda: self.add_category_from_entry(new_category_entry, manage_window))
        add_button.pack(pady=10)

    def add_category_from_entry(self, entry, window):
        new_category = entry.get().strip()
        if new_category and new_category not in self.categories:
            self.categories.append(new_category)
            self.custom_tools[new_category] = []
            self.save_custom_tools()
            self.rebuild_categories()
            tk.messagebox.showinfo("成功", f"已添加新分类：{new_category}")
            window.destroy()  # 关闭管理窗口
        elif new_category in self.categories:
            tk.messagebox.showerror("错误", "该分类已存在")
        else:
            tk.messagebox.showerror("错误", "分类名称不能为空")

    def rename_category(self, category):
        new_name = simpledialog.askstring("重命名分类", f"请输入 {category} 的新名称：")
        if new_name and new_name != category:
            if new_name not in self.categories:
                index = self.categories.index(category)
                self.categories[index] = new_name
                self.custom_tools[new_name] = self.custom_tools.pop(category)
                self.save_custom_tools()
                self.rebuild_categories()
                tk.messagebox.showinfo("成功", f"已将 {category} 重命名为 {new_name}")
            else:
                tk.messagebox.showerror("错误", "该分类名称已存在")

    def delete_category(self, category):
        if len(self.categories) > 1:  
            confirm = tk.messagebox.askyesno("确认删除", f"您确定要删除分类 '{category}' 吗？这将删除该分类下的所有工具。")
            if confirm:
                self.categories.remove(category)
                del self.custom_tools[category]
                self.save_custom_tools()
                self.rebuild_categories()
                tk.messagebox.showinfo("成功", f"已删除分类：{category}")
        else:
            tk.messagebox.showwarning("无法删除", "必须至少保留一个分类！")

    def rebuild_categories(self):
        for i in range(self.notebook.index("end")-1, 0, -1):
            self.notebook.forget(i)

        self.create_tool_categories()

    def manage_tools(self):
        manage_window = tk.Toplevel(self.master)
        manage_window.title("管理工具")
        manage_window.geometry("600x400")  # 增加窗口宽度

        notebook = ttk.Notebook(manage_window)
        notebook.pack(expand=True, fill="both", padx=5, pady=5)

        for category in self.categories:
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=category)

            canvas = tk.Canvas(frame)
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)

            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            for tool in self.custom_tools[category]:
                tool_frame = ttk.Frame(scrollable_frame)
                tool_frame.pack(fill="x", padx=5, pady=2)

                label = tk.Label(tool_frame, text=tool["name"], width=20, anchor="w")
                label.pack(side="left")

                edit_button = tk.Button(tool_frame, text="编辑", command=lambda t=tool, c=category: self.edit_tool(t, c))
                edit_button.pack(side="right")

                rename_button = tk.Button(tool_frame, text="重命名", command=lambda t=tool, c=category: self.rename_tool(t, c))
                rename_button.pack(side="right", padx=5)

                delete_button = tk.Button(tool_frame, text="删除", command=lambda t=tool, c=category: self.delete_tool(t, c))
                delete_button.pack(side="right", padx=5)

            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")

            add_button = tk.Button(frame, text="添加工具", command=lambda c=category: self.add_custom_tool(c))
            add_button.pack(pady=10)

    def edit_tool(self, tool, category):
        edit_window = tk.Toplevel(self.master)
        edit_window.title(f"编辑工具: {tool['name']}")
        edit_window.geometry("400x450")  # 调整窗口大小

        tk.Label(edit_window, text="工具路径:").pack(pady=(10, 0))
        path_entry = tk.Entry(edit_window, width=50)
        path_entry.insert(0, tool['path'])
        path_entry.pack(pady=(0, 10))

        tk.Label(edit_window, text="参数选项:").pack(pady=(10, 0))
        param_option_var = tk.StringVar(value=tool['param_option'])
        param_options = ["默认不添加参数", "默认添加参数", "每次打开都输入参数", "固定参数+目标"]
        for option in param_options:
            tk.Radiobutton(edit_window, text=option, variable=param_option_var, value=option).pack()

        tk.Label(edit_window, text="默认参数:").pack(pady=(10, 0))
        default_params_entry = tk.Entry(edit_window, width=50)
        default_params_entry.insert(0, tool.get('default_params', ''))
        default_params_entry.pack()

        tk.Label(edit_window, text="固定参数:").pack(pady=(10, 0))
        fixed_params_entry = tk.Entry(edit_window, width=50)
        fixed_params_entry.insert(0, tool.get('fixed_params', ''))
        fixed_params_entry.pack()

        new_window_var = tk.BooleanVar(value=tool.get('new_window', False))
        tk.Checkbutton(edit_window, text="新窗口打开", variable=new_window_var).pack(pady=(10, 0))

        def save_changes():
            tool['path'] = path_entry.get()
            tool['param_option'] = param_option_var.get()
            tool['default_params'] = default_params_entry.get()
            tool['fixed_params'] = fixed_params_entry.get()
            tool['new_window'] = new_window_var.get()
            self.save_custom_tools()
            edit_window.destroy()
            tk.messagebox.showinfo("成功", "工具设置已更新")

        save_button = tk.Button(edit_window, text="保存更改", command=save_changes)
        save_button.pack(pady=20)

    def rename_tool(self, tool, category):
        new_name = simpledialog.askstring("重命名工具", f"请输入 {tool['name']} 的新名称：")
        if new_name and new_name != tool['name']:
            tool['name'] = new_name
            self.save_custom_tools()
            self.rebuild_categories()
            tk.messagebox.showinfo("成功", f"工具已重命名为：{new_name}")

    def delete_tool(self, tool, category):
        confirm = tk.messagebox.askyesno("确认删除", f"您确定要删除工具 '{tool['name']}' 吗？")
        if confirm:
            self.custom_tools[category].remove(tool)
            self.save_custom_tools()
            self.rebuild_categories()
            tk.messagebox.showinfo("成功", f"已删除工具：{tool['name']}")

    async def load_single_plugin(self, filename):
        plugin_dir = os.path.join(os.getcwd(), 'extensions')
        plugin_path = os.path.join(plugin_dir, filename)
        spec = importlib.util.spec_from_file_location(filename[:-3], plugin_path)
        plugin = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plugin)
        
        if hasattr(plugin, 'Plugin'):
            plugin_instance = plugin.Plugin(self.plugins_frame)  
            self.plugins.append(plugin_instance)
            self.master.after(0, plugin_instance.create_ui)

    async def load_plugins_async(self):
        plugin_dir = os.path.join(os.getcwd(), 'extensions')
        if not os.path.exists(plugin_dir):
            os.makedirs(plugin_dir)
        
        tasks = []
        for filename in os.listdir(plugin_dir):
            if filename.endswith('.py'):
                tasks.append(self.load_single_plugin(filename))
        
        await asyncio.gather(*tasks)

    def load_plugins(self):
        asyncio.run(self.load_plugins_async())

    def manage_plugins(self):
        manage_window = tk.Toplevel(self.master)
        manage_window.title("管理插件")
        manage_window.geometry("400x300")

        canvas = tk.Canvas(manage_window)
        scrollbar = ttk.Scrollbar(manage_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for plugin in self.plugins:
            plugin_frame = ttk.Frame(scrollable_frame)
            plugin_frame.pack(fill="x", padx=5, pady=2)

            plugin_name = plugin.__class__.__module__.split('.')[-1]
            
            label = tk.Label(plugin_frame, text=f" {plugin_name}")
            label.pack(side="left")

            delete_button = tk.Button(plugin_frame, text="删除", command=lambda p=plugin, name=plugin_name: self.delete_plugin(p, name))
            delete_button.pack(side="right", padx=5)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        add_button = tk.Button(manage_window, text="添加插件", command=self.add_plugin)
        add_button.pack(pady=10)

    def add_plugin(self):
        file_path = tk.filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        if file_path:
            plugin_dir = os.path.join(os.getcwd(), 'extensions')
            dest_path = os.path.join(plugin_dir, os.path.basename(file_path))
            shutil.copy(file_path, dest_path)
            
            spec = importlib.util.spec_from_file_location(os.path.basename(file_path)[:-3], dest_path)
            plugin = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin)
            
            if hasattr(plugin, 'Plugin'):
                plugin_instance = plugin.Plugin(self.main_frame)
                self.plugins.append(plugin_instance)
                plugin_instance.create_ui()
                tk.messagebox.showinfo("成功", f"插件 {plugin_instance.__class__.__name__} 已添加")
            else:
                os.remove(dest_path)
                tk.messagebox.showerror("错误", "无效的插件文件")

    def delete_plugin(self, plugin, plugin_name):
        confirm = tk.messagebox.askyesno("确认删除", f"您确定要删除插件 '{plugin_name}' 吗？")
        if confirm:
            plugin_file = f"{plugin_name}.py"
            plugin_path = os.path.join(os.getcwd(), 'extensions', plugin_file)
            if os.path.exists(plugin_path):
                os.remove(plugin_path)
            self.plugins.remove(plugin)
            plugin.destroy()
            tk.messagebox.showinfo("成功", f"已删除插件：{plugin_name}")

root = tk.Tk()
app = PenetrationTestTool(root)

github_label = tk.Label(root, text="GitHub: @Norange1220", fg="blue", cursor="hand2")
github_label.pack(side="bottom", pady=5)

github_label.bind("<Button-1>", lambda e: open_github_link())

def open_github_link():
    import webbrowser
    webbrowser.open("https://github.com/Norange1220/N0range_tools")

root.mainloop()