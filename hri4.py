import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
import threading
import time
import random
import google.generativeai as genai

# Configure API key
GENAI_KEY = "AIzaSyBDXO5nCFHMd5KEO2P7B0v_soG3kTCJlgo"  # Replace with your actual Gemini API key
genai.configure(api_key=GENAI_KEY)
MODEL_NAME = 'gemini-2.0-flash' # Or 'gemini-pro-vision' if you want to process images.


class ChatbotGUI:
    """
    A simple GUI for a chatbot application.  This GUI provides a
    user interface for interacting with a chatbot.
    """
    def __init__(self, master):
        """
        Initializes the Chatbot GUI.

        Args:
            master (tk.Tk): The root window of the application.
        """
        self.master = master
        master.title("Chatbot")
       
        self.humor_styles = ["no humor","jokes", "sarcasm", "wordplay", "adaptive"]
        self.style = random.choice(self.humor_styles)
        self.chat = None
        self.is_running = True
        self.conversation_history = [] # added conversation history

        

        try:
            self.model = genai.GenerativeModel(MODEL_NAME)
            self.create_main_frame()
            self.update_prompt(0) #set the prompt

        except Exception as e:
            print(f"Error initializing model: {e}")
            self.model = None

    def create_main_frame(self):
        """Creates the main frame of the application."""
        self.main_frame = ttk.Frame(self.master)
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Add Label
        title_label = ttk.Label(self.main_frame, text="SOCIAL ROBOT CHAT", font=("TkDefaultFont", 16))
        title_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky=tk.N)

        # Create the text area for displaying messages.
        self.text_area = scrolledtext.ScrolledText(self.main_frame, wrap=tk.WORD,
                                                  state=tk.DISABLED, height=20, width=80, bg='lightgray')
        self.text_area.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

        # Create the entry field for typing messages.
        self.entry_field = tk.Entry(self.main_frame, width=50)
        self.entry_field.grid(row=2, column=0, padx=10, pady=5)

        # Create the send button.
        self.send_button = ttk.Button(self.main_frame, text="Send", command=self.send_message)
        self.send_button.grid(row=2, column=1, padx=10, pady=5)

        # Clear Chat Button
        self.clear_chat_button = ttk.Button(self.main_frame, text="Clear Chat", command=self.clear_chat)
        self.clear_chat_button.grid(row=2, column=2, columnspan=2, padx=5)

        # Create a label for status messages
        self.status_label = tk.Label(self.main_frame, text="Ready", anchor=tk.W)
        self.status_label.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)

        # Bind the Enter key to the send_message function.
        self.entry_field.bind("<Return>", self.send_message)

        # Settings Frame
        settings_frame = ttk.Frame(self.main_frame)
        settings_frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W)

        # Humor Style Label and Combobox
        humor_label = ttk.Label(settings_frame, text="Humor Style:")
        humor_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.humor_style_var = tk.StringVar()
        self.humor_style_combobox = ttk.Combobox(settings_frame, textvariable=self.humor_style_var, values=self.humor_styles)
        self.humor_style_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.humor_style_combobox.set(self.style)  # Initialize with current value

        
        # Apply button
        apply_button = ttk.Button(settings_frame, text="Apply", command=self.apply_settings)
        apply_button.grid(row=0, column=3, columnspan=2, padx=5, pady=10)

        # Status Labels
        self.humor_style_label = ttk.Label(self.main_frame, text=f"Active Humor Style: {self.style}", anchor=tk.W)
        self.humor_style_label.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)
        
       
        # Create a thread for handling chatbot responses.  This prevents the GUI
        # from freezing while the chatbot is processing.
        self.response_thread = threading.Thread(target=self.get_response)
        self.response_queue = []  # Use a queue to pass responses from the thread
        self.response_thread.daemon = True # Allow the program to exit even if this thread is running.
        self.response_thread.start()

        # Check for responses from the chatbot thread every 100ms
        #self.master.after(100, self.check_response_queue)

        # Add a protocol for when the window is closed.
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def apply_settings(self):
        """Applies the settings and updates the chatbot's behavior."""
        new_style = self.humor_style_var.get()
        
        if new_style != self.style:
            self.style = new_style
            self.update_prompt(1)
            self.chat = None
            # Update the labels
            self.humor_style_label.config(text=f"Active Humor Style: {self.style}")
            

   
    def update_prompt(self, display):
        """Update the initial prompt based on the selected style and presence."""
       
        style_instructions = {
            "no humor": "Greet a human user and describe your function in a professional, emotionless tone.",
            "jokes": "Greet a human user with a friendly tone and tell a short joke.",
            "sarcasm": "Greet a human user using dry, sarcastic humor, but remain friendly.",
            "wordplay": "Greet a human using puns and clever wordplay.",
            "adaptive": "Greet a human user in a tone that adapts to their mood and communication style. Begin neutral and adjust your tone to match the user's responses, using humor, warmth, sacarsm, wordplay or formality as appropriate."

        }
        user_prompt = f"{style_instructions[self.style]} Also describe your function as a robot."

        system_prompt = (
            "You are a socially interactive robot designed to engage with humans in different tones. "
            "You must maintain the assigned tone throughout the conversation."
        )
        self.full_prompt = f"{system_prompt}\n\n{user_prompt}"
        self.clear_chat()
        self.chat = self.model.start_chat()
        response = self.chat.send_message(self.full_prompt)
        response_text = response.text
        if(display==1):
            #messagebox.showinfo("Success","Humor style updated.")
            self.show_toast("Humor style selection successful!")


        self.master.after(0, self.display_message, "Chatbot", response_text)
        self.master.after(0, self.status_label.config, "Ready")

    def show_toast(self,message):
        toast = tk.Toplevel(root)
        toast.overrideredirect(True)
        toast.geometry("+{}+{}".format(root.winfo_x() + 150, root.winfo_y() + 350))
        tk.Label(toast, text=message, bg="lightgreen", padx=10, pady=5).pack()
        toast.after(1500, toast.destroy)  # Auto close after 1.5 sec


    def display_message(self, sender, message):
        """
        Displays a message in the text area.

        Args:
            sender (str): The sender of the message ("You" or "Chatbot").
            message (str): The message to display.
        """
        self.text_area.config(state=tk.NORMAL)  # Enable editing of the text area.
        self.text_area.insert(tk.END, f"{sender}: {message}\n")
        self.text_area.see(tk.END)  # Scroll to the end of the text area.
        self.text_area.config(state=tk.DISABLED)  # Disable editing of the text area.

    def send_message(self, event=None):
        """
        Sends the message from the entry field to the chatbot and displays it.
        The 'event' parameter is needed because the function is bound to the Enter key.
        """
        message = self.entry_field.get()
        if message:
            self.display_message("You", message)
            self.entry_field.delete(0, tk.END)  # Clear the entry field.
            self.response_queue.append(message) # Add message to queue for processing in thread.
            self.status_label.config(text="Processing...") # update the status

    def get_response(self):
        """
        Simulates getting a response from a chatbot.  This function is run in a
        separate thread to prevent the GUI from freezing.
        """
        while self.is_running:
            if self.response_queue:
                message = self.response_queue.pop(0) # Get the message from the queue
                # Simulate a delay for the chatbot to "think".
                #time.sleep(1)
                try:
                    # Get response from Gemini
                    if self.chat is None:
                        self.chat = self.model.start_chat()
                        
                    style_reminder = f"Remember: respond in the {self.style} style as configured."
                    prompt_with_reminder = f"{style_reminder}\nUser said: {message}"
                    response = self.chat.send_message(prompt_with_reminder)
                    response_text = response.text
                   
                    self.conversation_history.append({"role": "user", "parts": [{"text": message}]})
                    self.conversation_history.append({"role": "assistant", "parts": [{"text": response_text}]})
                except Exception as e:
                    response_text = f"Errorrr: {e}"
                    print(f"Error getting response from Gemini: {e}") # print the error

                self.master.after(0, self.display_message, "Chatbot", response_text)
                self.master.after(0, self.status_label.config, "Ready")
            time.sleep(0.1)  # Small sleep to reduce CPU usage

    def check_response_queue(self):
        """
        Checks the response queue and displays any new responses.  This
        function is called periodically by the main thread.
        """
        if self.response_queue:
            response = self.response_queue.pop(0)
            self.display_message("Chatbot", response)
            self.status_label.config(text="Ready")  # Update status after displaying

        if self.is_running:
            self.master.after(100, self.check_response_queue)  # Check again after 100ms

    def clear_chat(self):
        """Clears the chat history and text area."""
        self.text_area.config(state=tk.NORMAL)
        self.text_area.delete("1.0", tk.END)
        self.text_area.config(state=tk.DISABLED)
        self.conversation_history = []
        self.chat = None #clear the chat session


    def on_closing(self):
        """
        This function is called when the user closes the window.
        It stops the response thread and destroys the main window.
        """
        self.is_running = False  # Signal the thread to stop
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    gui = ChatbotGUI(root)
    root.mainloop()
