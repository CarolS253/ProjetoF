import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import os
import threading
import webbrowser
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from ttkbootstrap import Style

# Configuração do modelo
template = """
Answer the question below.

Here is the conversation history: {context}

Question: {question}

Answer:
"""
model = OllamaLLM(model="gemma2:2b")
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model


class ChatbotApp:
    def __init__(self, root):
        self.context = ""
        self.root = root 
        self.root.title("NatixisGPT - Assistente Virtual")
        self.root.geometry("700x500")
        self.root.resizable(False, False)

        try:
            root.iconbitmap("l.ico")
        except FileNotFoundError:
            print("Aviso: Ícone 'l.ico' não encontrado. Prosseguindo sem ícone.")

        # Estilo
        self.style = Style(theme="darkly")
        self.root = self.style.master

        # Modo escuro/claro
        self.is_dark_mode = True

        # Conversa
        self.chat_display = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, state='disabled', width=80, height=20,
            font=("Arial", 12), bg="#2e2e2e", fg="#ffffff"
        )
        self.chat_display.pack(padx=10, pady=10)

        # Entrada do texto
        frame_input = ttk.Frame(self.root)
        frame_input.pack(pady=10, padx=10, fill=tk.X)

        self.user_input = ttk.Entry(frame_input, width=50)
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)

        self.send_button = ttk.Button(frame_input, text="Enviar", command=self.send_message)
        self.send_button.pack(side=tk.RIGHT, padx=5, pady=5)

        self.user_input.focus()
        self.root.bind("<Return>", lambda event: self.send_message())

        # Menu
        self.create_menu()

        # Mensagem
        self.append_message("Bem-vindo ao NatixisGPT! Como posso ajuda-lo?\n")

    def create_menu(self):
        """Cria o menu da aplicação."""
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)

        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Nova Conversa", command=self.new_conversation)
        file_menu.add_command(label="Guardar Conversa", command=self.save_history)
        file_menu.add_command(label="Sair", command=self.quit_application)

        history_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Conversas", menu=history_menu)
        history_menu.add_command(label="Carregar Conversas", command=self.load_conversations)

        help_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Mudar Tema", command=self.toggle_mode)
        help_menu.add_command(label="Sobre Ollama", command=self.open_link)

    def open_link(self):
        """Abre o link no navegador."""
        url = "https://github.com/ollama/ollama"
        webbrowser.open(url)

    def new_conversation(self):
        """Inicia uma nova conversa."""
        if self.context:
            if messagebox.askyesno("Guardar Conversa", "Deseja guardar esta conversa?"):
                self.save_history()

        self.context = ""   
        self.chat_display.configure(state='normal')
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.configure(state='disabled')
        self.append_message("Nova conversa iniciada! Como posso ajudar-lo?\n")

    def toggle_mode(self):
        """Alterna entre modo claro e escuro."""
        if self.is_dark_mode:
            self.root.config(bg="#ffffff")
            self.chat_display.config(bg="#ffffff", fg="#000000")
            self.is_dark_mode = False
        else:
            self.root.config(bg="#2e2e2e")
            self.chat_display.config(bg="#2e2e2e", fg="#ffffff")
            self.is_dark_mode = True

    def send_message(self):
        """Obtém a mensagem do utilizador e processa a resposta."""
        user_message = self.user_input.get().strip()
        if not user_message:
            return

        if user_message.lower() == "exit":
            self.quit_application()

        self.append_message(f"You: {user_message}\n")
        self.user_input.delete(0, tk.END)
        self.user_input.config(state='disabled')
        self.send_button.config(state='disabled')

        threading.Thread(target=self.process_bot_response, args=(user_message,)).start()

    def process_bot_response(self, user_message):
        """Processa a resposta do chatbot."""
        try:
            result = chain.invoke({"context": self.context, "question": user_message})
        except Exception as e:
            result = f"Erro ao processar resposta: {e}"

        self.context += f"\nUser: {user_message}\nAI: {result}"
        self.append_message(f"Bot: {result}\n")

        self.user_input.config(state='normal')
        self.send_button.config(state='normal')

    def append_message(self, message):
        """Adiciona uma mensagem à exibição."""
        self.chat_display.configure(state='normal')
        self.chat_display.insert(tk.END, message)
        self.chat_display.configure(state='disabled')
        self.chat_display.see(tk.END)

    def save_history(self):
        """Salva o histórico da conversa."""
        title = simpledialog.askstring("Guardar Conversa", "Digite o título para esta conversa:")
        if title:
            title = title.replace(" ", "_")
            filename = f"{title}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.chat_display.get("1.0", tk.END))
            self.append_message(f"Histórico guardado como {filename}\n")

    def load_conversations(self):
        """Carrega conversas salvas."""
        saved_files = [f for f in os.listdir() if f.endswith('.txt')]
        if not saved_files:
            messagebox.showinfo("Sem Conversas", "Não existe conversas guardadas.")
            return

        selection_window = tk.Toplevel(self.root)
        selection_window.title("Selecione uma conversa")
        selection_window.geometry("400x300")

        listbox = tk.Listbox(selection_window, height=10)
        for file in saved_files:
            listbox.insert(tk.END, file)
        listbox.pack(pady=10)

        def on_select():
            selected_file = listbox.get(tk.ACTIVE)
            if selected_file:
                try:
                    with open(selected_file, "r", encoding="utf-8") as f:
                        history_content = f.read()
                    self.chat_display.configure(state='normal')
                    self.chat_display.delete(1.0, tk.END)
                    self.chat_display.insert(tk.END, history_content)
                    self.chat_display.configure(state='disabled')
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao carregar o histórico: {e}")
                selection_window.destroy()

        load_button = ttk.Button(selection_window, text="Carregar Conversa", command=on_select)
        load_button.pack(pady=10)

    def quit_application(self):
        """Fecha a aplicação."""
        if self.context:
            if messagebox.askyesno("Salvar Conversa", "Deseja guardar esta conversa?"):
                self.save_history()
        self.root.quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChatbotApp(root)
    root.mainloop()
