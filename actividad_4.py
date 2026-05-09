# -*- coding: UTF-8 -*-
import tkinter as tk
import os
from tkinter import messagebox, ttk

import eGela
import Dropbox
import helper
import time
from urllib.parse import unquote

##########################################################################################################

def make_entry(parent, caption, width=None, **options):
    label = tk.Label(parent, text=caption)
    label.pack(side=tk.TOP)
    entry = tk.Entry(parent, **options)
    entry.config(width=width)
    entry.pack(side=tk.TOP, padx=10, fill=tk.BOTH)
    return entry

def make_listbox(messages_frame):

    messages_frame.config(bd=1, relief="ridge")
    scrollbar = tk.Scrollbar(messages_frame)
    msg_listbox = tk.Listbox(messages_frame, height=20, width=70, exportselection=0, selectmode=tk.EXTENDED)
    msg_listbox.configure(yscrollcommand=scrollbar.set)
    scrollbar.configure(command=msg_listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    return msg_listbox

def transfer_files():
    global selected_items2
    if not selected_items1:
        messagebox.showwarning("Atención", "Por favor, selecciona un archivo de eGela para transferir.")
        return

    popup, progress_var, progress_bar = helper.progress("transfer_file", "Transfering files...")
    progress = 0
    progress_var.set(progress)
    progress_bar.update()
    progress_step = float(100.0 / len(selected_items1))

    for each in selected_items1:
        pdf_name, pdf_file = egela.get_pdf(each)

        progress_bar.update()
        newroot.update()

        if dropbox._path == "/":
            path = "/" + unquote(pdf_name)
            print ("----------------------: "+ pdf_name)
            print("----------------------: " + unquote(pdf_name))

        else:
            path = dropbox._path + "/" + pdf_name
        dropbox.transfer_file(path, pdf_file)

        progress += progress_step
        progress_var.set(progress)
        progress_bar.update()
        newroot.update()

        time.sleep(0.1)

    popup.destroy()
    selected_items2 = None  # Limpiamos el valor de la variable para que si luego intentamos eliminar un fichero/carpeta sin que haya nada seleccionado no pete
    dropbox.list_folder(msg_listbox2)
    msg_listbox2.yview(tk.END)

def delete_files():
    global selected_items2 # Necesario para poder limpiar la variable global

    if not selected_items2: #Querria decir que se está intentando borrar un fichero/carpeta sin seleccionar nada
        print("No hay archivos/carpetas seleccionados para eliminar.")
        messagebox.showwarning("Atención", "Por favor, selecciona al menos un archivo o carpeta para eliminar.")
        return

    popup, progress_var, progress_bar = helper.progress("delete_file", "Deleting files...")
    progress = 0
    progress_var.set(progress)
    progress_bar.update()
    progress_step = float(100.0 / len(selected_items2))

    for each in selected_items2:
        if dropbox._path == "/":
            path = "/" + dropbox._files[each]['name']
        else:
            path = dropbox._path + "/" + dropbox._files[each]['name']
            print (path)
        dropbox.delete_file(path)
        selected_items2 = None #Limpiamos el valor de la variable para que si luego intentamos eliminar un fichero/carpeta sin que haya nada seleccionado no pete
        progress += progress_step
        progress_var.set(progress)
        progress_bar.update()

    popup.destroy()

    dropbox.list_folder(msg_listbox2)

def name_folder(folder_name):
    if dropbox._path == "/":
        dropbox._path = dropbox._path + str(folder_name)
    else:
        dropbox._path = dropbox._path + '/' + str(folder_name)
    dropbox.create_folder(dropbox._path)
    var.set(dropbox._path)
    dropbox._root.destroy()
    dropbox.list_folder(msg_listbox2)

def create_folder():
    popup = tk.Toplevel(newroot)
    popup.geometry('200x100')
    popup.title('Dropbox')
    popup.iconbitmap('./favicon.ico')
    helper.center(popup)

    login_frame = tk.Frame(popup, padx=10, pady=10)
    login_frame.pack(fill=tk.BOTH, expand=True)

    label = tk.Label(login_frame, text="Create folder")
    label.pack(side=tk.TOP)
    entry_field = tk.Entry(login_frame, width=35)
    entry_field.bind("<Return>", name_folder)
    entry_field.pack(side=tk.TOP)
    send_button = tk.Button(login_frame, text="Send", command=lambda: name_folder(entry_field.get()))
    send_button.pack(side=tk.TOP)
    dropbox._root = popup


def share_file():
    global selected_items2

    # 1. Comprobamos si hay algún archivo seleccionado en Dropbox
    if not selected_items2:
        messagebox.showwarning("Atención", "Por favor, selecciona un archivo de Dropbox para compartir.")
        return
    if len(selected_items2) > 1:
        messagebox.showwarning("Atención", "Por favor, selecciona UN ÚNICO archivo de Dropbox para compartir.")
        print(selected_items2)
        return

    # Construimos la ruta del archivo que queremos compartir
    selection_index = selected_items2[0]
    selected_item = dropbox._files[selection_index]

    if dropbox._path == "/":
        path = "/" + dropbox._files[selection_index]['name']
    else:
        path = dropbox._path + "/" + dropbox._files[selection_index]['name']

    if selected_item['.tag'] == 'folder':
        messagebox.showwarning("Atención", "Actualmente solo se pueden compartir archivos individuales, no carpetas.")
        return

    shared_emails = dropbox.list_shared_members(path) # Obtenemos la lista de los emails con los que está compartido el fichero

    # Creamos el popup (más alto para que quepa la lista)
    popup = tk.Toplevel(newroot)
    popup.geometry('420x350')
    popup.title('Manage Sharing')
    popup.iconbitmap('./favicon.ico')
    helper.center(popup)

    # --- ZONA SUPERIOR: LISTA DE ACCESOS Y REVOCAR ---
    top_frame = tk.Frame(popup, padx=10, pady=10)
    top_frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(top_frame, text="Currently shared with:").pack(side=tk.TOP, anchor="w")

    # Contenedor para la lista y su scrollbar
    list_frame = tk.Frame(top_frame)
    list_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)

    scrollbar = tk.Scrollbar(list_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    members_listbox = tk.Listbox(list_frame, height=5, selectmode=tk.SINGLE, yscrollcommand=scrollbar.set)
    members_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=members_listbox.yview)

    # Rellenamos la lista con los emails obtenidos de Dropbox
    for email in shared_emails:
        members_listbox.insert(tk.END, email)

    # Botón Revocar (Rojo para indicar peligro)
    revoke_btn = tk.Button(top_frame, text="Remove Access", bg="#C6185C", fg="white",
                           command=lambda: execute_revoke(path, members_listbox, popup))
    revoke_btn.pack(side=tk.TOP, pady=5)

    # Separador visual
    ttk.Separator(popup, orient='horizontal').pack(fill='x', padx=10)

    # --- ZONA INFERIOR: AÑADIR NUEVO ACCESO ---
    bottom_frame = tk.Frame(popup, padx=10, pady=10)
    bottom_frame.pack(fill=tk.BOTH, expand=True)

    tk.Label(bottom_frame, text="Share with new email (Viewer):").pack(side=tk.TOP, anchor="w")

    entry_field = tk.Entry(bottom_frame, width=35)
    entry_field.pack(side=tk.TOP, pady=5)

    entry_field.bind("<Return>", lambda event: execute_share(path, entry_field.get(), popup))
    send_button = tk.Button(bottom_frame, text="Share",
                            command=lambda: execute_share(path, entry_field.get(), popup))
    send_button.pack(side=tk.TOP, pady=5)


def execute_revoke(path, listbox, popup):
    # Comprobamos qué elemento de la lista se ha seleccionado
    selection = listbox.curselection()
    if not selection:
        messagebox.showwarning("Atención", "Selecciona un email de la lista para revocar el acceso.")
        return

    email_to_remove = listbox.get(selection[0])

    # Pedimos confirmación
    respuesta = messagebox.askyesno("Confirmar",
                                    f"¿Estás seguro de que quieres quitar el acceso a:\n{email_to_remove}?")
    if respuesta:
        print(f"Revocando acceso a {email_to_remove}...")
        exito = dropbox.revoke_access(path, email_to_remove)

        if exito:
            messagebox.showinfo("Éxito", f"Acceso revocado correctamente a {email_to_remove}")
            popup.destroy()
        else:
            messagebox.showerror("Error",
                                 f"No se ha podido quitar el acceso a {email_to_remove}.\n\n(Asegúrate de no estar intentando borrar tu propio usuario).")

def execute_share(path, email, popup):
    global selected_items2

    #Comprobación básica por si le dan a OK sin escribir ningún email
    if not email.strip():
        messagebox.showwarning("Atención", "Por favor, introduce un email válido.")
        return

    print(f"Intentando compartir '{path}'")

    # Llamamos a la función de la clase Dropbox
    exito = dropbox.share_file(path, email)
    if exito:
        # Cerramos el popup, limpiamos la selección para evitar el "IndexError" y mostramos aviso
        popup.destroy()
        selected_items2 = None
        messagebox.showinfo("Éxito", f"Petición enviada.\nEmail: {email}\n")
    else:
        messagebox.showerror("Error",
                             "Hubo un problema al compartir el archivo.\n\nComprueba que el correo existe y tiene formato válido.")

##########################################################################################################

def check_credentials(event= None):
    egela.check_credentials(username, password)

def on_selecting1(event):
    global selected_items1
    widget = event.widget
    selected_items1 = widget.curselection()
    print (selected_items1)

def on_selecting2(event):
    global selected_items2
    widget = event.widget
    selected_items2 = widget.curselection()
    print (selected_items2)

def on_double_clicking2(event):
    widget = event.widget
    selection = widget.curselection()
    if selection[0] == 0 and dropbox._path != "/":
        head, tail = os.path.split(dropbox._path)
        dropbox._path = head
    else:
        selected_file = dropbox._files[selection[0]]
        if selected_file['.tag'] == 'folder':
            if dropbox._path == "/":
                dropbox._path = dropbox._path + selected_file['name']
            else:
                dropbox._path = dropbox._path + '/' + selected_file['name']
    var.set(dropbox._path)
    dropbox.list_folder(msg_listbox2)
##########################################################################################################
# Login eGela
root = tk.Tk()
root.geometry('250x150')
root.iconbitmap('./favicon.ico') #
root.title('Login eGela')
helper.center(root)
egela = eGela.eGela(root)

login_frame = tk.Frame(root, padx=10, pady=10)
login_frame.pack(fill=tk.BOTH, expand=True)

username = make_entry(login_frame, "User name:", 16)
password = make_entry(login_frame, "Password:", 16, show="*")
password.bind("<Return>", check_credentials)

button = tk.Button(login_frame, borderwidth=4, text="Login", width=10, pady=8, command=check_credentials)
button.pack(side=tk.BOTTOM)

root.mainloop()

if not egela._login:
    exit()
# Si nos logeamos en eGela cogemos las referencias a los pdfs
pdfs = egela.get_pdf_refs()

##########################################################################################################
# Login Dropbox
root = tk.Tk()
root.geometry('250x100')
root.iconbitmap('./favicon.ico')
root.title('Login Dropbox')
helper.center(root)

login_frame = tk.Frame(root, padx=10, pady=10)
login_frame.pack(fill=tk.BOTH, expand=True)
# Login and Authorize in Drobpox
dropbox = Dropbox.Dropbox(root)

label = tk.Label(login_frame, text="Login and Authorize\nin Drobpox")
label.pack(side=tk.TOP)
button = tk.Button(login_frame, borderwidth=4, text="Login", width=10, pady=8, command=dropbox.do_oauth)
button.pack(side=tk.BOTTOM)

root.mainloop()

##########################################################################################################
# eGela -> Dropbox

newroot = tk.Tk()
newroot.geometry("850x400")
newroot.iconbitmap('./favicon.ico') #
newroot.title("eGela -> Dropbox") #
helper.center(newroot)

newroot.rowconfigure(0, weight=1)
newroot.rowconfigure(1, weight=5)
newroot.columnconfigure(0, weight=6)
newroot.columnconfigure(1, weight=1)
newroot.columnconfigure(2, weight=6)
newroot.columnconfigure(3, weight=1)

# Etigueta PDFs en Sistemas Web (0,0)   #
var2 = tk.StringVar()
var2.set("PDFs en Sistemas Web")
label2 = tk.Label(newroot, textvariable=var2)
label2.grid(column=0, row=0, ipadx=5, ipady=5)

# Etigueta del directorio de Dropbox (0,2)
var = tk.StringVar()
var.set(dropbox._path)
label = tk.Label(newroot, textvariable=var)
label.grid( row=0, column=2, ipadx=5, ipady=5)

# Frame con lista de PDFs e eGela (1,0)
selected_items1 = None
messages_frame1 = tk.Frame(newroot)
msg_listbox1 = make_listbox(messages_frame1)
msg_listbox1.bind('<<ListboxSelect>>', on_selecting1)
msg_listbox1.pack(side=tk.LEFT, fill=tk.BOTH)
#messages_frame1.pack()
messages_frame1.grid(row=1, column=0, ipadx=10, ipady=10, padx=2, pady=2) #

# Frame con boton >>> (1,1)
frame1 = tk.Frame(newroot)
button1 = tk.Button(frame1, borderwidth=4, text=">>>", width=10, pady=8, command=transfer_files)
button1.pack()
frame1.grid(row=1, column=1, ipadx=5, ipady=5)

# Frame con ficheros en Dropbox (1,2)
selected_items2 = None
messages_frame2 = tk.Frame(newroot)
msg_listbox2 = make_listbox(messages_frame2)
msg_listbox2.bind('<<ListboxSelect>>', on_selecting2)
msg_listbox2.bind('<Double-Button-1>', on_double_clicking2)
msg_listbox2.pack(side=tk.RIGHT, fill=tk.BOTH)

#messages_frame2.pack()
messages_frame2.grid(row=1, column=2, ipadx=10, ipady=10, padx=2, pady=2)

# Frame con botones Create y Delete (1,3)

frame2 = tk.Frame(newroot)
button2 = tk.Button(frame2, borderwidth=4,  background="#C6185C",fg="white", text="Delete", width=10, pady=8, command=delete_files)
button2.pack(padx=2, pady=2)
button3 = tk.Button(frame2, borderwidth=4, background="#7C86FF",fg="white", text="Create folder", width=10, pady=8, command=create_folder)
button3.pack(padx=2, pady=2)
button4 = tk.Button(frame2, borderwidth=4, background="#0C8E00",fg="white", text="Share file", width=10, pady=8, command=share_file)
button4.pack(padx=2, pady=2)
frame2.grid(row=1, column=3,  ipadx=10, ipady=10)

for each in pdfs:
    msg_listbox1.insert(tk.END, each['pdf_name'])
    msg_listbox1.yview(tk.END)

dropbox.list_folder(msg_listbox2)

newroot.mainloop()