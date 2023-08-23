import LangChainEngine as LCE
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import pinecone
from time import localtime, strftime
from os.path import exists
import json as json

class LCUI:
    def __init__(self):

        self.configpath = 'config/config.json'
        self.configexists = exists(self.configpath)

        self.openaikey = self.pineconekey = self.pineconeenv = None
        self.readconfig()

        # CREATE GUI
        # Setting Window
        self.root = tk.Tk()
        self.root.geometry("600x500")
        self.root.title("PDFQuery")
        self.root.resizable(False, False)

        self.style = ttk.Style()
        self.style.theme_use("default")

        self.topmenu = tk.Menu(self.root)
        self.root.config(menu=self.topmenu)

        self.options = tk.Menu(self.topmenu)
        self.topmenu.add_cascade(label="Settings", menu=self.options)
        self.options.add_command(label="Config", command=self.setconfig)
        self.options.add_separator()
        self.options.add_command(label="Exit", command=self.root.quit)

        ### HEADER ###
        # Header title of Application (Parent: Root)
        self.headertitle = ttk.Label(self.root, text="PDF Uploader and Query", font=('Arial', 36))
        self.headertitle.pack(padx=20)

        # Grid Frame to put Index Selector in (Parent: Root)
        self.headerindexframe = ttk.Frame(self.root)
        self.headerindexframe.columnconfigure(0, weight=1)
        self.headerindexframe.columnconfigure(1, weight=1)
        self.headerindexframe.pack(fill='x')

        # Label for Header Index Selector (Parent: HeaderIndexFrame)
        self.headerindexlabel = ttk.Label(self.headerindexframe, text="Index:", font=("Arial", 14))
        self.headerindexlabel.grid(row=0, column=0, sticky="e")

        # Index Selector (Parent: HeaderIndexFrame)
        self.headerindexreference = ttk.Combobox(self.headerindexframe, values=self.getallindexes(True))
        self.headerindexreference.set("Choose Index")
        self.headerindexreference.grid(row=0, column=1, sticky="w", padx=20, pady=5)\

        # Grid Frame for the Query and Upload Sections (Parent: Root)
        self.menuframe = ttk.Frame(self.root)
        self.menuframe.columnconfigure(0,weight=1)
        self.menuframe.columnconfigure(1,weight=1)

        ### Notebook ###
        self.notebook = ttk.Notebook(self.menuframe)

        ### Upload Frame ###
        # Upload Section Grid Frame for Label and Entry (Parent: MenuFrame)
        self.uploadframe = ttk.Frame(self.notebook)
        self.uploadframe.grid(row=0, column=0, sticky='n', padx=5, pady=5)

        ### Query Frame ###
        # Query Section Grid Frame for Label and Entry (Parent: MenuFrame)
        self.queryframe = ttk.Frame(self.notebook)
        self.queryframe.grid(row=0, column=1, sticky='n', padx=5, pady=5)

        ### Upload Section ###
        # Section Label (Parent: UploadFrame)
        self.uploadlabel = ttk.Label(self.uploadframe, text="Upload PDF to Pinecone", font=("Arial", 14))
        self.uploadlabel.grid(row=0, column=0, sticky="we", pady=5)

        # Grid Frame for Uploading Label and Entry (Parent: UploadFrame)
        self.uploadentryframe = ttk.Frame(self.uploadframe)
        self.uploadentryframe.columnconfigure(0, weight=1)
        self.uploadentryframe.columnconfigure(1, weight=8)
        self.uploadentryframe.grid(row=1, column=0, sticky="we", pady=5)

        # PDF URL/PATH Label (Parent: UploadEntryFrame)
        self.urllabel = ttk.Label(self.uploadentryframe, text="PDF:", font=("Arial", 8))
        self.urllabel.grid(row=0, column=0, sticky="e")

        # PDF URL/PATH Entry (Parent: UploadEntryFrame)
        self.pdfreference = ttk.Entry(self.uploadentryframe)
        self.pdfreference.bind("<KeyPress>", lambda event: self.submit(event, 'upload'))
        self.pdfreference.grid(row=0, column=1, sticky="we", padx=20, pady=5)

        # Upload Button (Parent: UploadFrame)
        self.btnupload = ttk.Button(self.uploadframe, text="Upload PDF", command=self.start_uploadPDFButton)
        self.btnupload.grid(row=2, column=0, pady=5)

        # Information Box where Status and Index Information is printed (Parent: UploadFrame)
        self.indexinfobox = tk.Text(self.uploadframe, height=10, font=("Arial", 10), state='disabled')
        self.indexinfobox.grid(row=3, column=0, padx=20, pady=5)

        # Button to request Index Information (Parent: UploadFrame)
        self.btngetinfo = ttk.Button(self.uploadframe, text="Get index Info", command=self.getindexinfo)
        self.btngetinfo.grid(row=4, column=0, pady=5)

        ### Query Section ###
        # Section Label (Parent: QueryFrame)
        self.querylabel = ttk.Label(self.queryframe, text="Query PDF from Pinecone", font=("Arial", 14))
        self.querylabel.grid(row=0, column=0, sticky="we", pady=5)

        # Grid Frame for Query Label and Entry (Parent: QueryFrame)
        self.queryentryframe = ttk.Frame(self.queryframe)
        self.queryentryframe.columnconfigure(0, weight=1)
        self.queryentryframe.columnconfigure(1, weight=8)
        self.queryentryframe.grid(row=1, column=0, sticky="we", pady=5)

        # Query Label (Parent: QueryEntryFrame)
        self.querylabel = ttk.Label(self.queryentryframe, text="Query:", font=("Arial", 8))
        self.querylabel.grid(row=0, column=0, sticky="e")

        # Query Entry (Parent: QueryEntryFrame)
        self.querybox = ttk.Entry(self.queryentryframe)
        self.querybox.bind("<KeyPress>", lambda event: self.submit(event, 'query'))
        self.querybox.grid(row=0, column=1, sticky="we", padx=20, pady=5)

        # Query Button (Parent: QueryFrame)
        self.btnquery = ttk.Button(self.queryframe, text="Query PDF", command=self.start_queryPDFButton)
        self.btnquery.grid(row=2, column=0, pady= 5)

        # Query Response (Parent: QueryFrame)
        self.queryresponse = tk.Text(self.queryframe, height=12, font=("Arial", 10), state='disabled')
        self.queryresponse.grid(row=3, column=0, padx=20, pady=5, sticky='we')

        self.notebook.add(self.uploadframe, text="Upload")
        self.notebook.add(self.queryframe, text="Query")
        self.notebook.grid(row=0, column=0)

        self.menuframe.pack(fill='both')

        self.root.after(0, self.initialize_and_run)
        self.root.mainloop()

    def readconfig(self):
        if(self.configexists):
            with open(self.configpath, 'r') as config:
                data = json.load(config)
                self.openaikey = data["OPENAI"]["key"]
                self.pineconekey = data["PINECONE"]["key"]
                self.pineconeenv = data["PINECONE"]["env"]
        return

    def setconfig(self):

        popup = tk.Toplevel(self.root)
        popup.title("Config Settings")
        popup.geometry("300x150")

        openailabel = ttk.Label(popup, text="OpenAI")
        openailabel.pack()
        openaiframe = ttk.Frame(popup)
        openaiframe.columnconfigure(0, weight=1)
        openaiframe.columnconfigure(1, weight=6)
        openaiframe.pack()
        openaikeylabel = ttk.Label(openaiframe, text="Key")
        openaikeylabel.grid(row=0, column=0, sticky='e')
        openaikeyentry = ttk.Entry(openaiframe)
        if(self.configexists): openaikeyentry.insert(0, self.openaikey)
        openaikeyentry.grid(row=0, column=1)

        pineconelabel = ttk.Label(popup, text="Pinecone")
        pineconelabel.pack()
        pineconeframe = ttk.Frame(popup)
        pineconeframe.columnconfigure(0, weight=1)
        pineconeframe.columnconfigure(1, weight=6)
        pineconeframe.pack()
        pineconekeylabel = ttk.Label(pineconeframe, text="Key")
        pineconekeylabel.grid(row=0, column=0, sticky='e')
        pineconekeyentry = ttk.Entry(pineconeframe)
        if(self.configexists): pineconekeyentry.insert(0, self.pineconekey)
        pineconekeyentry.grid(row=0, column=1)
        pineconeenvlabel = ttk.Label(pineconeframe, text="Environment")
        pineconeenvlabel.grid(row=1, column=0, sticky='e')
        pineconeenventry = ttk.Entry(pineconeframe)
        if(self.configexists): pineconeenventry.insert(0, self.pineconeenv)
        pineconeenventry.grid(row=1, column=1)

        btnsaveconfig = ttk.Button(popup, text="Save", command=lambda:self.saveconfig(popup, openaikeyentry.get(), pineconekeyentry.get(), pineconeenventry.get()))
        btnsaveconfig.pack()
        return
    
    def saveconfig(self, configwindow, openaikey, pineconekey, pineconeenv):
        if(len(openaikey)!= 0 and len(pineconekey) != 0 and len(pineconeenv) != 0):
            config_entries = {
                "OPENAI": {
                    "key": openaikey
                },
                "PINECONE":{
                    "key": pineconekey,
                    "env": pineconeenv
                }
            }
            print(self.configexists)
            match self.configexists:
                case True:
                    with open(self.configpath, 'w+') as config:
                        data = json.load(config)
                        newdata = {
                            "OPENAI": {
                                "key": config_entries["OPENAI"]["key"]
                            },
                            "PINECONE": {
                                "key": config_entries["PINECONE"]["key"],
                                "env": config_entries["PINECONE"]["env"]                        }
                        }
                        json.dump(newdata, config, indent=2, sort_keys=True)
                        pass
                case False:
                    with open(self.configpath, 'w') as config:
                        data = {
                            "OPENAI": {
                                "key": config_entries["OPENAI"]["key"]
                            },
                            "PINECONE": {
                                "key": config_entries["PINECONE"]["key"],
                                "env": config_entries["PINECONE"]["env"]
                            }
                        }
                        json.dump(data, config, indent=2, sort_keys=True)
                        pass
            print (config_entries)
            configwindow.destroy()
            return
        else:
            errormessage = ""
            for i, e in enumerate([openaikey, pineconekey, pineconeenv]):
                if(len(e) == 0):
                    if(i != 0):
                        errormessage += ", "
                    match i:
                        case 0:
                            errormessage += "Open AI key"
                        case 1:
                            errormessage += "Pinecone key"
                        case 2:
                            errormessage += "Pinecone Environment"
            errormessage += " fields cannot be empty!"
            messagebox.showerror(title="ERROR", message=f"{errormessage}")

    def getallindexes(self, addnone): # Lists out all Indexes. Bool adds '--None--' in list
        pinecone.init(
            api_key=LCE.SERVICE["PINECONE"]["key"],
            environment=LCE.SERVICE["PINECONE"]["env"]
        )

        index_list = pinecone.list_indexes()
        return_value = index_list
        # print(return_value)

        if addnone:
            return_value.append('--None--')

        # print(return_value)

        return return_value

    def getindexinfo(self): # Print Index Information
        self.indexinfobox.configure(state='normal')
        self.indexinfobox.delete('1.0', tk.END)

        try:

            # indexes = self.getallindexes(False)
            # print(indexes)

            information = f"Time: {strftime('%H:%M:%S', localtime())}\n"
            information += "Index Info:\n"

            # for index_name in indexes:
            index_name = self.headerindexreference.get()
            index_info = pinecone.describe_index(index_name)
            index_stats = pinecone.Index(index_name).describe_index_stats()

            information += f"    Index Name: {index_name}\n"
            information += f"    Vector Count: {index_stats.total_vector_count}\n"
            information += f"    dimension: {index_info.dimension}\n"
            information += f"    Metric: {index_info.metric}\n"
            information += "\n"

            self.indexinfobox.insert('1.0', information)

        except Exception as e:
            self.indexinfobox.insert('1.0', f"Error fetching index information: {str(e)}")

        finally:
            self.indexinfobox.configure(state='disabled')
        return

    def updateuploadstatus(self, status): # Updates the Uploading Status
        self.indexinfobox.configure(state='normal')
        self.indexinfobox.delete('1.0', tk.END)
        self.indexinfobox.insert('1.0', f"Upload Status: {status}")
        self.indexinfobox.configure(state='disabled')
        return

    def start_uploadPDFButton(self):
        self.url = self.pdfreference.get()
        self.uploadPDFButton(self.embeddings, self.url)
        return

    def uploadPDFButton(self, embeddings, url):
        self.updateuploadstatus("Uploading...")
        self.updateuploadstatus(LCE.uploadPDF(embeddings, url))
        return

    def start_queryPDFButton(self):
        self.query = self.querybox.get()
        self.queryPDFButton(self.embeddings, self.index, self.query)
        return
        
    def queryPDFButton(self, embeddings, index, query):
        self.queryresponse.configure(state='normal')
        self.querybox.delete(0, tk.END)
        self.queryresponse.delete('1.0', tk.END)
        chain_result = LCE.queryPDF(embeddings, index, query)
        self.queryresponse.insert('1.0', chain_result) 
        self.queryresponse.configure(state='disabled')
        return

    def submit(self, event, location): # If Enter/Return is pressed
        if event.state == 0 and event.keysym == 'Return':
            match location:
                case 'query':
                    self.start_queryPDFButton() # Run this function if location on Enter/Return pressed is in Query Section
                case 'upload':
                    self.start_uploadPDFButton() # Run this function if location on Enter/Return pressed in in Upload Section
        return
                    
    def initialize_and_run(self):
        self.embeddings, self.index = self.initialize_pinecone()
        self.root.mainloop()
        return

    def initialize_pinecone(self):
        embeddings, index =  LCE.initialize_pinecone()
        return embeddings, index

ui = LCUI()