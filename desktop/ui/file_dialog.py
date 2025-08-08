import os
import platform
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

def show_file_chooser(on_files_selected, title="Select file(s)", start_path=None, multiselect=True):
    """
    Abre um popup com FileChooser e botões Open/Cancel.
    - on_files_selected: callback que recebe uma lista de paths selecionados.
    - multiselect True por padrão.
    """
    if start_path is None:
        # Inicia na home do usuário (Windows: C:\Users\<user>\)
        start_path = os.path.expanduser("~")

    chooser = FileChooserListView(path=start_path, multiselect=multiselect)

    # Botões na parte inferior
    btn_open = Button(text="Open", size_hint=(1, None), height=40)
    btn_cancel = Button(text="Cancel", size_hint=(1, None), height=40)
    btn_row = BoxLayout(size_hint_y=None, height=40)
    btn_row.add_widget(btn_open)
    btn_row.add_widget(btn_cancel)

    # Conteúdo do popup: chooser + botões
    content = BoxLayout(orientation="vertical")
    content.add_widget(chooser)
    content.add_widget(btn_row)

    popup = Popup(title=title, content=content, size_hint=(0.9, 0.9))

    def _do_open(instance):
        selection = list(chooser.selection)
        if selection:
            try:
                on_files_selected(selection)
            except Exception as e:
                # Não queremos quebrar o app aqui; log para debug
                print("show_file_chooser: erro no callback on_files_selected:", e)
        popup.dismiss()

    def _do_cancel(instance):
        popup.dismiss()

    btn_open.bind(on_press=_do_open)
    btn_cancel.bind(on_press=_do_cancel)

    popup.open()
