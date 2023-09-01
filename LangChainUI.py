from typing import List
# from langchain_utils import uploadPDF, queryPDF
from updated_langchain_utils_final_modified import uploadPDF, queryPDF
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
import pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from time import localtime, strftime
from os.path import exists
import json as json
from dotwiz import DotWiz, make_dot_wiz

class LCUI:
    def __init__(self):

        self.configpath = 'config/config.json'
        self.configexists = None
        self.checkconfigexists()

        self.embeddings = self.index = self.openaikey = self.pineconekey = self.pineconeenv = self.lastindex = self.index_list = None
        self.readconfig()

        # CREATE GUI
        # Setting Window
        self.root = tk.Tk()
        self.root.geometry("600x500")
        self.root.title("PDFQuery")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.style = ttk.Style()
        self.style.theme_use("default")

        self.topmenu = tk.Menu(self.root)
        self.root.config(menu=self.topmenu)

        self.options = tk.Menu(self.topmenu, tearoff=0)
        self.topmenu.add_cascade(label="Options", menu=self.options)
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
        self.headerindexreference = ttk.Combobox(self.headerindexframe, values=self.getallindexes(addnone=True))
        combobox_element = self.lastindex if self.lastindex in self.getallindexes(addnone=False) else "--None--"
        self.headerindexreference.set(combobox_element)
        self.headerindexreference.grid(row=0, column=1, sticky="w", padx=20, pady=5)\

        # Grid Frame for the Query and Upload Sections (Parent: Root)
        self.menuframe = ttk.Frame(self.root)
        self.menuframe.columnconfigure(0,weight=1)
        self.menuframe.columnconfigure(1,weight=1)

        ### Notebook ###
        self.notebook = ttk.Notebook(self.menuframe)

        ### Create Index Frame ###
        # Create Index Grid Frame for Label and Entry (Parent: MenuFrame)
        self.createindexframe = ttk.Frame(self.notebook)
        self.createindexframe.grid(row=0, column=0, sticky='n', padx=5, pady=5)

        ### Upload Frame ###
        # Upload Section Grid Frame for Label and Entry (Parent: MenuFrame)
        self.uploadframe = ttk.Frame(self.notebook)
        self.uploadframe.grid(row=0, column=0, sticky='n', padx=5, pady=5)

        ### Query Frame ###
        # Query Section Grid Frame for Label and Entry (Parent: MenuFrame)
        self.queryframe = ttk.Frame(self.notebook)
        self.queryframe.grid(row=0, column=1, sticky='n', padx=5, pady=5)

        ### Create Index Section ###
        # Section Label (Parent: CreateIndexFrame)
        self.createindexlabel = ttk.Label(self.createindexframe, text="Create new Index on Pinecone", font=("Arial", 14))
        self.createindexlabel.grid(row=0, column=0, sticky="we", pady=5)

        # Grid Frame for Creating Index Label and Inputs (Parent: CreateIndexFrame)
        self.createindexinputframe = ttk.Frame(self.createindexframe)
        self.createindexinputframe.columnconfigure(0, weight=1)
        self.createindexinputframe.columnconfigure(1, weight=8)
        self.createindexinputframe.grid(row=1, column=0, sticky="we", pady=5)

        # Create Index name Label (Parent: CreateIndexInputFrame)
        self.createindexnamelabel = ttk.Label(self.createindexinputframe, text="Index Name:", font=("Arial", 8))
        self.createindexnamelabel.grid(row=0, column=0, sticky='e')

        # Create Index name Entry (Parent: CreateIndexInputFrame)
        self.createindexname = ttk.Entry(self.createindexinputframe)
        self.createindexname.grid(row=0, column=1, sticky='we', padx=20, pady=5)

        # Create Index dimension Label (Parent: CreateIndexInputFrame)
        self.createindexdimensionlabel = ttk.Label(self.createindexinputframe, text="Dimension:", font=("Arial", 8))
        self.createindexdimensionlabel.grid(row=1, column=0, sticky='e')

        # Create Index dimension Entry (Parent: CreateIndexInputFrame)
        self.createindexdimension = ttk.Entry(self.createindexinputframe)
        self.createindexdimension.insert(0,"1536")
        self.createindexdimension.grid(row=1, column=1, sticky='we', padx=20, pady= 5)

        # Create Index metric Label (Parent: CreateIndexInputFrame)
        self.createindexmetriclabel = ttk.Label(self.createindexinputframe, text="Metric", font=("Arial", 8))
        self.createindexmetriclabel.grid(row=2, column=0, sticky='e')

        # Create Index metric Combobox (Parent: CreateIndexInputFrame)
        self.createindexmetric = ttk.Combobox(self.createindexinputframe, values=["euclidean", "cosine", "dotproduct"])
        self.createindexmetric.set("cosine")
        self.createindexmetric.grid(row=2, column=1, sticky="we", padx=20, pady=5)

        # Create Index pod type Label (Parent: CreateIndexInputFrame)
        self.createindexpodtypelabel = ttk.Label(self.createindexinputframe, text="Pod Type:", font=("Arial", 8))
        self.createindexpodtypelabel.grid(row=3, column=0, sticky='e')

        # Create Index pod type Combobox (Parent: CreateIndexInputFrame)
        self.createindexpodtype = ttk.Combobox(self.createindexinputframe, values=["s1.x1", "s1.x2", "s1.x4", "s1.x8", "p1.x1", "p1.x2", "p1.x4", "p1.x8", "p2.x1", "p2.x2", "p2.x4", "p2.x8"])
        self.createindexpodtype.set("p1.x1")
        self.createindexpodtype.grid(row=3, column=1, sticky="we", padx=20, pady=5)

        # Create Index button (Parent: CreateIndexInputFrame)
        self.btncreateindex = ttk.Button(self.createindexinputframe, text="Create Index", command=self.createindex)
        self.btncreateindex.grid(row=4, column=0, sticky='e', pady=5)

        # Create Index Error Box (Parent: CreateIndexInputFrame)
        self.createindexerrorbox = tk.Text(self.createindexinputframe, height=6, font=("Arial", 10), wrap=tk.WORD, state=tk.DISABLED)
        self.createindexerrorbox.grid(row=4, column=1, sticky='we', padx=20, pady=5)

        ### Upload Section ###
        # Section Label (Parent: UploadFrame)
        self.uploadlabel = ttk.Label(self.uploadframe, text="Upload PDF to Pinecone", font=("Arial", 14))
        self.uploadlabel.grid(row=0, column=0, sticky="we", padx=5, pady=5)

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
        self.indexinfobox = tk.Text(self.uploadframe, height=10, font=("Arial", 10),wrap=tk.WORD, state=tk.DISABLED)
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
        self.queryresponse = tk.Text(self.queryframe, height=12, font=("Arial", 10),wrap=tk.WORD, state=tk.DISABLED)
        self.queryresponse.grid(row=3, column=0, padx=20, pady=5, sticky='we')

        self.notebook.add(self.queryframe, text="Query")
        self.notebook.add(self.uploadframe, text="Upload")
        self.notebook.add(self.createindexframe, text="Create Index")
        self.notebook.grid(row=0, column=0)

        self.menuframe.pack(fill='both')

        self.root.after(0, self.initialize_and_run)
        self.root.mainloop()

    def edit_textbox(self, box: tk.Text, string: str, isdelete: bool):
        box.configure(state=tk.NORMAL)
        if(isdelete):
            box.delete('1.0', tk.END)
        box.insert('1.0', string)
        box.configure(state=tk.DISABLED)
        return

    def createindex(self):
        try:
            pinecone.create_index(name=self.createindexname.get(), dimension=int(self.createindexdimension.get()), metric=self.createindexmetric.get(), pod_type=self.createindexpodtype.get())
        
        except Exception as e:
            self.edit_textbox(self.createindexerrorbox, f"Error creating index: {str(e)}", True)
        return

    def checkconfigexists(self):
        self.configexists = exists(self.configpath)
        return

    def readconfig(self):
        if(self.configexists):
            with open(self.configpath, 'r') as config:
                data = DotWiz(json.load(config))
                self.openaikey = data.SERVICES.OPENAI.key
                self.pineconekey = data.SERVICES.PINECONE.key
                self.pineconeenv = data.SERVICES.PINECONE.env

                self.lastindex = data.SETTINGS.lastindex
        return

    def setserviceconfig(self, parent, format):
        serviceidx = 0
        serviceelements = []
        for service in format:
            if serviceidx != 0: serviceidx += 1
            label = ttk.Label(parent, text=format[service].section)
            label.grid(row=serviceidx, column=0)
            serviceidx += 1
            frame = ttk.Frame(parent)
            frame.columnconfigure(0, weight=1)
            frame.columnconfigure(1, weight=6)
            frame.grid(row=serviceidx, column=0)

            fieldidx = 0
            fieldelements = []
            for field in format[service]:
                if(field != "section"):
                    fieldlabel = ttk.Label(frame, text=format[service][field].field)
                    fieldlabel.grid(row=fieldidx, column=0, sticky='e')
                    fieldentry = ttk.Entry(frame, width=60)
                    format[service][field].entry = fieldentry
                    if(self.configexists): fieldentry.insert(0, format[service][field].value)
                    fieldentry.grid(row=fieldidx, column=1)
                    fieldelements.append(fieldlabel, fieldentry)
                    fieldidx += 1
            serviceelements.append(label, fieldelements)
        return serviceelements
    
    def setindexesconfig(self, parent):
        indexidx = 0
        indexelements = []
        with open(self.configpath, 'r') as config:
            data = DotWiz(json.load(config))
            for index in data.SETTINGS.INDEXES.keys():
                label = ttk.Label(parent, text=index)
                label.grid(row=indexidx, column=0)
                entry = ttk.Entry(parent, width=60)
                entry.insert(0, data.SETTINGS.INDEXES[index].url)
                entry.grid(row=indexidx, column=1, pady=5)
                indexelements.append((label, entry))
                indexidx += 1

        return indexelements

    def setconfig(self):

        self.checkconfigexists()
        self.readconfig()

        popup = tk.Toplevel(self.root)
        popup.title("Config Settings")
        popup.geometry("500x200")

        notebook = ttk.Notebook(popup)

        serviceframe = ttk.Frame(notebook)
        serviceframe.columnconfigure(0, weight=1)
        indexesframe = ttk.Frame(notebook)
        indexesframe.columnconfigure(0, weight=1)

        serviceformat = DotWiz({
            "OPENAI": {
                "section": "OpenAI",
                "key": {
                    "field": "key",
                    "value": self.openaikey,
                    "entry": None
                }
            },
            "PINECONE": {
                "section": "Pinecone",
                "key": {
                    "field": "key",
                    "value": self.pineconekey,
                    "entry": None
                },
                "env": {
                    "field": "env",
                    "value": self.pineconeenv,
                    "entry": None
                }
            }
        })

        serviceelements = self.setserviceconfig(parent=serviceframe, format=serviceformat)
        
        servicesaveframe = ttk.Frame(serviceframe)
        btnsaveconfig = ttk.Button(servicesaveframe, text="SAVE", command=lambda:self.saveserviceconfig(elements=serviceelements, label=savestatusentry))
        btnsaveconfig.grid(row=0, column=0, padx=5, pady=5)
        savestatusentry = ttk.Label(servicesaveframe, text="Don't forget to save!", font=("Arial", 8))
        savestatusentry.grid(row=0, column=1, padx=5, pady=5)
        servicesaveframe.grid(row=len(serviceformat.keys())*2, column=0)

        serviceframe.pack(fill=tk.BOTH, ipadx=10, ipady=10)

        indexelements = self.setindexesconfig(parent=indexesframe)

        indexessaveframe = ttk.Frame(indexesframe)
        btnsaveconfig = ttk.Button(indexessaveframe, text="SAVE", command=lambda:self.saveindexesconfig(elements=indexelements, label=savestatusentry))
        btnsaveconfig.grid(row=0, column=0, padx=5, pady=5)
        savestatusentry = ttk.Label(indexessaveframe, text="Don't forget to save!", font=("Arial", 8))
        savestatusentry.grid(row=0, column=1, padx=5, pady=5)
        indexessaveframe.grid(row=len(serviceformat.keys())*2, column=0)

        indexesframe.pack(fill=tk.BOTH, ipadx=10, ipady=10)
        notebook.add(serviceframe, text="Services")
        notebook.add(indexesframe, text="Indexes")
        notebook.pack(fill=tk.BOTH)

        return
    
    def saveindexesconfig(self, elements, label):
        if self.configexists:
            with open(self.configpath, 'r') as config:
                data = DotWiz(json.load(config))
                newdata = DotWiz({"INDEXES":[]})

                for index in elements:
                    dwv = make_dot_wiz([("url", index[1])])
                    dw = make_dot_wiz([(index[0], dwv)])
                    newdata.INDEXES.append(dw)

                data.SETTINGS = newdata
            with open(self.configpath, 'w') as config:
                json.dump(data.to_dict(), config, indent=2, sort_keys=True)
        else:
            with open(self.configpath, 'w') as config:
                data = DotWiz(json.load(config))
                newdata = DotWiz({"INDEXES": []})

                for index in elements:
                    dwv = make_dot_wiz([("url", index[1])])
                    dw = make_dot_wiz([(index[0], dwv)])
                    newdata.INDEXES.append(dw)

                data.SETTINGS = newdata
                
                json.dump(data.to_dict(), config, indent=2, sort_keys=True)
        label["text"] = "Saved!"

        return
    
    def saveserviceconfig(self, elements, label):
        notemptycheck = []
        for entries in elements[1]:
            if type(entries) == ttk.Entry:
                notemptycheck.append(len(entries.get()) != 0)
        ispass = not(False in notemptycheck)

        if(ispass):
            

        if len(openaikey) != 0 and len(pineconekey) != 0 and len(pineconeenv) != 0:
            config_entries = DotWiz({
                "OPENAI": {
                    "key": openaikey
                },
                "PINECONE": {
                    "key": pineconekey,
                    "env": pineconeenv
                }
            })

            if self.configexists:
                with open(self.configpath, 'r') as config:
                    data = DotWiz(json.load(config))
                    data.SERVICES.OPENAI.key = config_entries.OPENAI.key
                    data.SERVICES.PINECONE.key = config_entries.PINECONE.key
                    data.SERVICES.PINECONE.env = config_entries.PINECONE.env
                with open(self.configpath, 'w') as config:
                    json.dump(data, config, indent=2, sort_keys=True)
            else:
                with open(self.configpath, 'w') as config:
                    data = json.load(config)
                    data.SERVICES.OPENAI.key = config_entries.SERVICES.OPENAI.key
                    data.SERVICES.PINECONE.key = config_entries.SERVICES.PINECONE.key
                    data.SERVICES.PINECONE.env = config_entries.SERVICES.PINECONE.env
                    
                    json.dump(data, config, indent=2, sort_keys=True)
            label["text"] = "Saved!"
        else:
            errormessage = ""
            plural = ""
            n = 0
            for e in [openaikey, pineconekey, pineconeenv]:
                if len(e) == 0:
                    if n != 0:
                        errormessage += ", "
                        plural = "s"
                    match n:
                        case 0:
                            errormessage += "Open AI key"
                        case 1:
                            errormessage += "Pinecone key"
                        case 2:
                            errormessage += "Pinecone Environment"
                    n += 1
            errormessage += f" field{plural} cannot be empty!"
            messagebox.showerror(title="ERROR", message=f"{errormessage}")
            label["text"] = "Error"


    def getallindexes(self, addnone: bool) -> List[str]: # Lists out all Indexes. Bool adds '--None--' in list
        pinecone.init(
            api_key=self.pineconekey,
            environment=self.pineconeenv
        )

        self.index_list = pinecone.list_indexes()
                
        return_value = self.index_list
        # print(return_value)

        if addnone:
            return_value.append('--None--')

        # print(return_value)

        return return_value

    def getindexinfo(self): # Print Index Information
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

            self.edit_textbox(self.indexinfobox, information, True)

        except Exception as e:
            self.edit_textbox(self.indexinfobox, f"Error fetching index information: {str(e)}", True)

        return

    def updateuploadstatus(self, status: str): # Updates the Uploading Status
        self.edit_textbox(self.indexinfobox, f"Upload Status: {status}", True)
        return

    def start_uploadPDFButton(self):
        self.url = self.pdfreference.get()
        self.updateuploadstatus("Uploading...")
        self.updateuploadstatus(uploadPDF(indexname=self.headerindexreference.get(), embeddings=self.embeddings, pdf=self.url))
        return

    def start_queryPDFButton(self):
        self.query = self.querybox.get()
        chain_result = queryPDF(path=self.configpath, openaikey=self.openaikey, embeddings=self.embeddings, index=self.index, indexname=self.headerindexreference.get(), query=self.query)
        self.edit_textbox(box=self.queryresponse, string=chain_result, isdelete=True),
        self.querybox.delete(0, tk.END)
        return

    def submit(self, event, location: str): # If Enter/Return is pressed
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
        pinecone.init(
            api_key = self.pineconekey,
            environment = self.pineconeenv
        )
        embeddings = OpenAIEmbeddings(openai_api_key=self.openaikey)
        index = pinecone.Index(index_name=self.headerindexreference.get())

        return embeddings, index
    
    def on_closing(self):
        with open(self.configpath, 'r+') as config:
            data = json.load(config)

            data["SETTINGS"]["lastindex"] = self.headerindexreference.get()

            config.seek(0)
            json.dump(data, config, indent=2, sort_keys=True)
            # config.truncate()
        self.root.destroy()
        return

def get_lcui_instance():
    return LCUI()

ui = LCUI()