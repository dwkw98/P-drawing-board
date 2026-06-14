from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.colorpicker import ColorPicker
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.graphics import Color, Line, Rectangle
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.core.text import LabelBase
from kivy.clock import Clock
import os

# 添加中文字体支持
from kivy.utils import platform

if platform == 'android':
    DEFAULT_FONT = "/system/fonts/NotoSansCJK-Regular.ttc"
elif platform == 'win':
    DEFAULT_FONT = "C:/Windows/Fonts/msyh.ttc"
elif platform == 'linux':
    DEFAULT_FONT = "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf"
else:
    DEFAULT_FONT = None

if DEFAULT_FONT and os.path.exists(DEFAULT_FONT):
    LabelBase.register(name='CustomFont', fn_regular=DEFAULT_FONT)
    from kivy.config import Config
    Config.set('kivy', 'default_font', ['CustomFont'])


class DrawingWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_color = [1, 1, 1, 1]
        self.current_size = 5
        self.is_eraser = False
        self.background_image = None
        self.history = []
        self.history_index = -1
        self.current_line = None
        self.save_current_state()
        
    def save_current_state(self):
        """保存当前状态"""
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        
        self.history.append([instr for instr in self.canvas.children[:]])
        self.history_index += 1
        
        if len(self.history) > 30:
            self.history.pop(0)
            self.history_index -= 1
    
    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.restore_state()
            
    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.restore_state()
            
    def restore_state(self):
        self.canvas.clear()
        if self.background_image:
            with self.canvas:
                Rectangle(pos=self.pos, size=self.size, texture=self.background_image.texture)
        for instr in self.history[self.history_index]:
            self.canvas.add(instr)
    
    def set_color(self, color):
        self.current_color = color
        self.is_eraser = False
        
    def set_eraser(self):
        self.is_eraser = True
        
    def set_brush_size(self, size):
        self.current_size = size
        
    def clear_all(self):
        self.canvas.clear()
        self.save_current_state()
        
    def load_image(self, path):
        try:
            img = CoreImage(path)
            self.background_image = img
            self.canvas.clear()
            with self.canvas:
                Rectangle(pos=self.pos, size=self.size, texture=img.texture)
            self.save_current_state()
            return True
        except Exception as e:
            print(f"加载图片失败: {e}")
            return False
    
    def real_save_image(self, filename):
        """真正保存图片到文件"""
        try:
            self.export_to_png(filename)
            if os.path.exists(filename) and os.path.getsize(filename) > 0:
                return True
            return False
        except Exception as e:
            print(f"保存失败: {e}")
            return False
        
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            color = self.current_color if not self.is_eraser else [1, 1, 1, 1]
            with self.canvas:
                Color(color[0], color[1], color[2], color[3] if len(color) > 3 else 1)
                self.current_line = Line(points=(touch.x, touch.y), width=self.current_size)
            return True
            
    def on_touch_move(self, touch):
        if hasattr(self, 'current_line') and self.current_line:
            self.current_line.points += (touch.x, touch.y)
            return True
            
    def on_touch_up(self, touch):
        if hasattr(self, 'current_line') and self.current_line:
            self.current_line = None
            self.save_current_state()
            return True


class DrawingApp(App):
    def build(self):
        if platform != 'android':
            Window.size = (800, 600)
        
        self.main_layout = BoxLayout(orientation='vertical')
        
        # 工具栏
        toolbar = BoxLayout(size_hint=(1, 0.1), spacing=5, padding=5)
        
        color_btn = Button(text='Color')
        color_btn.bind(on_press=self.show_color_picker)
        
        eraser_btn = Button(text='Eraser')
        eraser_btn.bind(on_press=self.activate_eraser)
        
        undo_btn = Button(text='Undo')
        undo_btn.bind(on_press=self.undo_action)
        
        redo_btn = Button(text='Redo')
        redo_btn.bind(on_press=self.redo_action)
        
        clear_btn = Button(text='Clear')
        clear_btn.bind(on_press=self.clear_canvas)
        
        import_btn = Button(text='Import')
        import_btn.bind(on_press=self.import_image)
        
        save_btn = Button(text='Save')
        save_btn.bind(on_press=self.save_drawing)
        
        size_label = Label(text='Size:', size_hint=(0.1, 1))
        size_slider = Slider(min=1, max=20, value=5, size_hint=(0.2, 1))
        size_slider.bind(value=self.change_brush_size)
        
        toolbar.add_widget(color_btn)
        toolbar.add_widget(eraser_btn)
        toolbar.add_widget(undo_btn)
        toolbar.add_widget(redo_btn)
        toolbar.add_widget(clear_btn)
        toolbar.add_widget(import_btn)
        toolbar.add_widget(save_btn)
        toolbar.add_widget(size_label)
        toolbar.add_widget(size_slider)
        
        self.drawing_widget = DrawingWidget()
        
        self.main_layout.add_widget(toolbar)
        self.main_layout.add_widget(self.drawing_widget)
        
        return self.main_layout
    
    def show_color_picker(self, instance):
        content = BoxLayout(orientation='vertical')
        color_picker = ColorPicker()
        
        def set_color(instance):
            self.drawing_widget.set_color(color_picker.color)
            popup.dismiss()
        
        btn_layout = BoxLayout(size_hint=(1, 0.2))
        select_btn = Button(text='Select')
        select_btn.bind(on_press=set_color)
        cancel_btn = Button(text='Cancel')
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        
        btn_layout.add_widget(select_btn)
        btn_layout.add_widget(cancel_btn)
        
        content.add_widget(color_picker)
        content.add_widget(btn_layout)
        
        popup = Popup(title='Pick Color', content=content, size_hint=(0.9, 0.9))
        popup.open()
        
    def activate_eraser(self, instance):
        self.drawing_widget.set_eraser()
        
    def change_brush_size(self, instance, value):
        self.drawing_widget.set_brush_size(value)
        
    def undo_action(self, instance):
        self.drawing_widget.undo()
        
    def redo_action(self, instance):
        self.drawing_widget.redo()
        
    def clear_canvas(self, instance):
        self.drawing_widget.clear_all()
        
    def import_image(self, instance):
        content = BoxLayout(orientation='vertical')
        
        if platform == 'android':
            start_path = '/storage/emulated/0/DCIM'
        else:
            start_path = '.'
            
        filechooser = FileChooserListView(path=start_path)
        filechooser.filters = ['*.png', '*.jpg', '*.jpeg']
        
        def load_selected(instance):
            if filechooser.selection:
                if self.drawing_widget.load_image(filechooser.selection[0]):
                    popup.dismiss()
                    self.show_message("Success", "Image loaded!")
                else:
                    self.show_message("Error", "Failed to load")
                
        btn_layout = BoxLayout(size_hint=(1, 0.1))
        load_btn = Button(text='Load')
        load_btn.bind(on_press=load_selected)
        cancel_btn = Button(text='Cancel')
        cancel_btn.bind(on_press=lambda x: popup.dismiss())
        
        btn_layout.add_widget(load_btn)
        btn_layout.add_widget(cancel_btn)
        
        content.add_widget(filechooser)
        content.add_widget(btn_layout)
        
        popup = Popup(title='Select Image', content=content, size_hint=(0.9, 0.9))
        popup.open()
        
    def save_drawing(self, instance):
        from kivy.uix.textinput import TextInput
        
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # 文件名输入
        filename_input = TextInput(text='mydrawing', hint_text='filename', size_hint=(1, 0.3))
        
        def do_save(instance):
            filename = filename_input.text.strip()
            if not filename:
                filename = "mydrawing"
            
            # 构建保存路径
            if platform == 'android':
                save_dir = '/storage/emulated/0/Pictures'
                # 尝试创建子目录
                drawing_dir = os.path.join(save_dir, 'DrawingApp')
                try:
                    if not os.path.exists(drawing_dir):
                        os.makedirs(drawing_dir)
                    save_dir = drawing_dir
                except:
                    pass  # 使用 Pictures 目录
            else:
                save_dir = '.'
            
            # 完整文件路径
            full_path = os.path.join(save_dir, f"{filename}.png")
            
            # 如果文件已存在，添加数字后缀
            counter = 1
            original_path = full_path
            while os.path.exists(full_path):
                full_path = os.path.join(save_dir, f"{filename}_{counter}.png")
                counter += 1
            
            # 保存图片
            if self.drawing_widget.real_save_image(full_path):
                save_popup.dismiss()
                self.show_message("Success", f"Saved to:\n{full_path}", duration=2)
            else:
                self.show_message("Error", "Failed to save image!")
        
        # 按钮
        btn_layout = BoxLayout(size_hint=(1, 0.3), spacing=10)
        save_btn = Button(text='Save')
        save_btn.bind(on_press=do_save)
        cancel_btn = Button(text='Cancel')
        cancel_btn.bind(on_press=lambda x: save_popup.dismiss())
        
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)
        
        content.add_widget(filename_input)
        content.add_widget(btn_layout)
        
        save_popup = Popup(title='Save Drawing', content=content, size_hint=(0.8, 0.3))
        save_popup.open()
    
    def show_message(self, title, message, duration=1.5):
        """显示提示消息"""
        content = Label(text=message)
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.3))
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), duration)


if __name__ == '__main__':
    DrawingApp().run()
