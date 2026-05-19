"""Tkinter user interface for Steel Tycoon."""

import tkinter as tk
from tkinter import ttk, messagebox

from config import AI_ARCHETYPES, ARCHETYPE_ORDER, CONTRACT_TEMPLATES, PRODUCTION_METHODS, TECHNOLOGIES
from game_state import GameState
from localization import LANGUAGE_LABELS, display_option, language_code_from_label, parse_option, tr
from persistence import delete_save_file, list_save_files, load_game_state, save_game_state


class MarketTycoonApp(tk.Tk):
    # Tkinter shell that switches between menu, setup, settings, and game screens.
    def __init__(self):
        super().__init__()

        self.language = "en"
        self.font_scale = 1.0
        self.title(tr(self.language, "app_title"))
        self.geometry("1280x860")
        self.resizable(True, True)
        
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "TNotebook",
            background="#f0f0f0",
            borderwidth=0
        )

        style.configure(
            "TNotebook.Tab",
            padding=[12, 6],
            background="#e0e0e0",
            foreground="black"
        )

        style.map(
            "TNotebook.Tab",
            background=[("selected", "#ffffff")],
            foreground=[("selected", "black")]
        )

        style.configure(
            "TCombobox",
            fieldbackground="white",
            background="white",
            foreground="black",
            arrowcolor="black"
        )

        self.current_frame = None

        self.show_start_screen()

    def font(self, size, weight=None):
        scaled_size = max(8, int(round(size * self.font_scale)))
        if weight:
            return ("Arial", scaled_size, weight)
        return ("Arial", scaled_size)

    def t(self, key, **kwargs):
        return tr(self.language, key, **kwargs)

    def set_language(self, language):
        self.language = language
        self.title(self.t("app_title"))

        if hasattr(self, "game_state"):
            self.game_state.language = language

    def force_redraw(self):
        self.update_idletasks()

        if self.current_frame is not None:
            self.current_frame.update_idletasks()

        width = self.winfo_width()
        height = self.winfo_height()

        if width > 1 and height > 1:
            self.geometry(f"{width + 1}x{height}")
            self.update_idletasks()
            self.geometry(f"{width}x{height}")
    
    def clear_frame(self):
        if self.current_frame is not None:
            self.current_frame.destroy()

    def switch_frame(self, frame_class):
        self.clear_frame()
        if hasattr(self, "game_state"):
            self.game_state.language = self.language
        self.current_frame = frame_class(self)
        self.current_frame.pack(fill="both", expand=True)
        self.after_idle(self.force_redraw)
        self.after(100, self.force_redraw)

    def show_start_screen(self):
        self.switch_frame(StartScreen)

    def show_new_game_screen(self):
        self.switch_frame(NewGameScreen)

    def show_load_game_screen(self):
        self.switch_frame(LoadGameScreen)

    def show_settings_screen(self):
        self.switch_frame(SettingsScreen)

    def show_game_screen(self):
        self.switch_frame(GameScreen)


class StartScreen(tk.Frame):
    # Main menu screen for starting, loading, settings, or exiting.
    def __init__(self, master):
        super().__init__(master)

        title = tk.Label(
            self,
            text=master.t("app_title"),
            font=master.font(32, "bold")
        )
        title.pack(pady=80)

        subtitle = tk.Label(
            self,
            text=master.t("subtitle"),
            font=master.font(14)
        )
        subtitle.pack(pady=10)

        button_frame = tk.Frame(self)
        button_frame.pack(pady=50)

        new_game_button = tk.Button(
            button_frame,
            text=master.t("new_game"),
            width=25,
            height=2,
            command=master.show_new_game_screen
        )
        new_game_button.pack(pady=10)

        load_game_button = tk.Button(
            button_frame,
            text=master.t("load_game"),
            width=25,
            height=2,
            command=master.show_load_game_screen
        )
        load_game_button.pack(pady=10)

        settings_button = tk.Button(
            button_frame,
            text=master.t("settings"),
            width=25,
            height=2,
            command=master.show_settings_screen
        )
        settings_button.pack(pady=10)

        exit_button = tk.Button(
            button_frame,
            text=master.t("exit"),
            width=25,
            height=2,
            command=master.destroy
        )
        exit_button.pack(pady=10)


class NewGameScreen(tk.Frame):
    # New game setup screen for scenario, difficulty, company name, and AI choices.
    def __init__(self, master):
        super().__init__(master)

        title = tk.Label(
            self,
            text=master.t("new_game_setup"),
            font=master.font(26, "bold")
        )
        title.pack(pady=30)

        form_frame = tk.Frame(self)
        form_frame.pack(pady=20)
        self.form_row = 0

        self.scenario_var = tk.StringVar(value=display_option("19th Century", master.language))
        self.difficulty_var = tk.StringVar(value=display_option("Normal", master.language))
        self.ai_count_var = tk.IntVar(value=6)
        self.start_cash_var = tk.IntVar(value=10000)
        self.turn_limit_var = tk.StringVar(value="120")
        self.company_name_var = tk.StringVar(value="Player Steel Works")
        self.show_ai_stats_var = tk.BooleanVar(value=True)
        self.strategy_vars = []
        self.custom_only_widgets = []

        self.create_label_and_entry(
            form_frame,
            master.t("company_name"),
            self.company_name_var
        )

        self.scenario_box = self.create_label_and_option(
            form_frame,
            master.t("scenario"),
            self.scenario_var,
            [display_option(option, master.language) for option in ["19th Century", "Custom"]]
        )
        self.scenario_box.bind("<<ComboboxSelected>>", self.update_scenario_fields)

        self.create_label_and_option(
            form_frame,
            master.t("difficulty"),
            self.difficulty_var,
            [display_option(option, master.language) for option in ["Easy", "Normal", "Hard"]]
        )

        self.ai_count_spinbox = self.create_label_and_spinbox(
            form_frame,
            master.t("ai_count"),
            self.ai_count_var,
            1,
            6
        )
        self.custom_only_widgets.append(self.ai_count_spinbox)

        self.cash_spinbox = self.create_label_and_spinbox(
            form_frame,
            master.t("starting_cash"),
            self.start_cash_var,
            5000,
            50000,
            increment=1000
        )
        self.custom_only_widgets.append(self.cash_spinbox)

        self.turn_limit_box = self.create_label_and_option(
            form_frame,
            master.t("turn_limit"),
            self.turn_limit_var,
            ["60", "120", "240", display_option("Infinite", master.language)]
        )
        self.custom_only_widgets.append(self.turn_limit_box)

        show_ai_checkbox = tk.Checkbutton(
            form_frame,
            text=master.t("show_ai_stats"),
            variable=self.show_ai_stats_var
        )
        show_ai_checkbox.grid(row=self.form_row, column=1, sticky="w", pady=10)
        self.custom_only_widgets.append(show_ai_checkbox)
        self.form_row += 1

        self.note_label = tk.Label(
            form_frame,
            text=master.t("fixed_19c_note"),
            font=master.font(10),
            fg="#555555"
        )
        self.note_label.grid(row=self.form_row, column=0, columnspan=2, pady=(6, 10))
        self.form_row += 1

        for index, archetype in enumerate(ARCHETYPE_ORDER, start=1):
            strategy_var = tk.StringVar(value=display_option(archetype, master.language))
            self.strategy_vars.append(strategy_var)
            strategy_box = self.create_label_and_option(
                form_frame,
                master.t("ai_strategy", index=index),
                strategy_var,
                [display_option(option, master.language) for option in ARCHETYPE_ORDER]
            )
            self.custom_only_widgets.append(strategy_box)

        self.update_scenario_fields()

        button_frame = tk.Frame(self)
        button_frame.pack(pady=40)

        start_button = tk.Button(
            button_frame,
            text=master.t("start_game"),
            width=20,
            height=2,
            command=self.start_game
        )
        start_button.grid(row=0, column=0, padx=10)

        back_button = tk.Button(
            button_frame,
            text=master.t("back"),
            width=20,
            height=2,
            command=master.show_start_screen
        )
        back_button.grid(row=0, column=1, padx=10)

    def create_label_and_option(self, parent, label_text, variable, options):
        row = self.form_row
        self.form_row += 1

        label = tk.Label(parent, text=label_text, font=self.master.font(12))
        label.grid(row=row, column=0, sticky="e", padx=10, pady=10)

        option = ttk.Combobox(
            parent,
            textvariable=variable,
            values=options,
            state="readonly",
            width=25
        )
        option.grid(row=row, column=1, sticky="w", padx=10, pady=10)
        option.label = label
        return option

    def create_label_and_spinbox(self, parent, label_text, variable, from_value, to_value, increment=1):
        row = self.form_row
        self.form_row += 1

        label = tk.Label(parent, text=label_text, font=self.master.font(12))
        label.grid(row=row, column=0, sticky="e", padx=10, pady=10)

        spinbox = tk.Spinbox(
            parent,
            from_=from_value,
            to=to_value,
            increment=increment,
            textvariable=variable,
            width=25
        )
        spinbox.grid(row=row, column=1, sticky="w", padx=10, pady=10)
        spinbox.label = label
        return spinbox

    def create_label_and_entry(self, parent, label_text, variable):
        row = self.form_row
        self.form_row += 1

        label = tk.Label(parent, text=label_text, font=self.master.font(12))
        label.grid(row=row, column=0, sticky="e", padx=10, pady=10)

        entry = tk.Entry(parent, textvariable=variable, width=28)
        entry.grid(row=row, column=1, sticky="w", padx=10, pady=10)
        return entry

    def update_scenario_fields(self, event=None):
        scenario = parse_option(self.scenario_var.get(), self.master.language)
        is_custom = scenario == "Custom"

        self.ai_count_var.set(self.ai_count_var.get() if is_custom else 6)

        for widget in self.custom_only_widgets:
            if is_custom:
                widget.grid()
            else:
                widget.grid_remove()
            
            if hasattr(widget, "label"):
                if is_custom:
                    widget.label.grid()
                else:
                    widget.label.grid_remove()

        self.note_label.grid() if not is_custom else self.note_label.grid_remove()

    def start_game(self):
        settings = {
            "player_name": self.company_name_var.get().strip() or "Player Company",
            "scenario": parse_option(self.scenario_var.get(), self.master.language),
            "difficulty": parse_option(self.difficulty_var.get(), self.master.language),
            "ai_count": self.ai_count_var.get(),
            "ai_archetypes": [
                parse_option(strategy_var.get(), self.master.language)
                for strategy_var in self.strategy_vars[:self.ai_count_var.get()]
            ],
            "start_cash": self.start_cash_var.get(),
            "max_turns": self.parse_turn_limit(),
            "show_ai_stats": self.show_ai_stats_var.get(),
            "language": self.master.language
        }

        if settings["scenario"] == "19th Century":
            settings["ai_count"] = 6
            settings["ai_archetypes"] = ARCHETYPE_ORDER[:]
            settings["max_turns"] = 120
        elif len(settings["ai_archetypes"]) != len(set(settings["ai_archetypes"])):
            messagebox.showerror(
                self.master.t("invalid_input_title"),
                self.master.t("duplicate_strategy")
            )
            return

        self.master.game_settings = settings

        self.master.game_state = GameState(
        scenario=settings["scenario"],
        difficulty=settings["difficulty"],
        ai_count=settings["ai_count"],
        ai_archetypes=settings["ai_archetypes"],
        start_cash=settings["start_cash"],
        player_name=settings["player_name"],
        max_turns=settings["max_turns"],
        show_ai_stats=settings["show_ai_stats"],
        language=settings["language"]
    )

        self.master.show_game_screen()

    def parse_turn_limit(self):
        value = self.turn_limit_var.get()
        if parse_option(value, self.master.language) == "Infinite":
            return None
        return int(value)


class LoadGameScreen(tk.Frame):
    # Save browser screen that loads or deletes JSON save files.
    def __init__(self, master):
        super().__init__(master)

        title = tk.Label(
            self,
            text=master.t("load_game"),
            font=master.font(26, "bold")
        )
        title.pack(pady=30)

        info = tk.Label(
            self,
            text=master.t("saved_games_info"),
            font=master.font(14)
        )
        info.pack(pady=20)

        self.save_listbox = tk.Listbox(self, width=60, height=12)
        self.save_listbox.pack(pady=20)

        self.refresh_save_list()

        button_frame = tk.Frame(self)
        button_frame.pack(pady=20)

        load_button = tk.Button(
            button_frame,
            text=master.t("load_selected_save"),
            width=20,
            height=2,
            command=self.load_selected_save
        )
        load_button.grid(row=0, column=0, padx=10)

        delete_button = tk.Button(
            button_frame,
            text=master.t("delete_selected_save"),
            width=20,
            height=2,
            command=self.delete_selected_save
        )
        delete_button.grid(row=0, column=1, padx=10)

        back_button = tk.Button(
            button_frame,
            text=master.t("back"),
            width=20,
            height=2,
            command=master.show_start_screen
        )
        back_button.grid(row=0, column=2, padx=10)

    def load_selected_save(self):
        selection = self.save_listbox.curselection()

        if not selection:
            messagebox.showwarning(self.master.t("no_save_selected_title"), self.master.t("no_save_selected"))
            return

        selected_save = self.save_listbox.get(selection[0])
        if selected_save == self.master.t("no_saves_found"):
            return

        try:
            self.master.game_state = load_game_state(selected_save)
            self.master.game_state.language = self.master.language
        except (OSError, json.JSONDecodeError, KeyError, ValueError) as error:
            messagebox.showerror(self.master.t("load_failed"), str(error))
            return

        messagebox.showinfo(self.master.t("load_game"), self.master.t("loading_save", save=selected_save))

        self.master.show_game_screen()

    def delete_selected_save(self):
        selection = self.save_listbox.curselection()

        if not selection:
            messagebox.showwarning(self.master.t("no_save_selected_title"), self.master.t("no_save_selected"))
            return

        selected_index = selection[0]
        selected_save = self.save_listbox.get(selected_index)
        if selected_save == self.master.t("no_saves_found"):
            return

        confirm = messagebox.askyesno(
            self.master.t("delete_save_title"),
            self.master.t("delete_save_confirm", save=selected_save)
        )

        if confirm:
            delete_save_file(selected_save)
            self.refresh_save_list()

    def refresh_save_list(self):
        self.save_listbox.delete(0, tk.END)
        save_files = list_save_files()

        if not save_files:
            self.save_listbox.insert(tk.END, self.master.t("no_saves_found"))
            return

        for save in save_files:
            self.save_listbox.insert(tk.END, save)


class SettingsScreen(tk.Frame):
    # Settings screen for resolution, language, and font scaling.
    def __init__(self, master):
        super().__init__(master)

        title = tk.Label(
            self,
            text=master.t("settings"),
            font=master.font(26, "bold")
        )
        title.pack(pady=40)

        resolution_frame = tk.Frame(self)
        resolution_frame.pack(pady=20)

        label = tk.Label(
            resolution_frame,
            text=master.t("window_resolution"),
            font=master.font(14)
        )
        label.grid(row=0, column=0, padx=10)

        self.resolution_var = tk.StringVar(value="1280x860")

        resolution_box = ttk.Combobox(
            resolution_frame,
            textvariable=self.resolution_var,
            values=["1024x768", "1280x720", "1280x860", "1366x768", "1600x900"],
            state="readonly",
            width=20
        )
        resolution_box.grid(row=0, column=1, padx=10)

        language_frame = tk.Frame(self)
        language_frame.pack(pady=20)

        language_label = tk.Label(
            language_frame,
            text=master.t("language"),
            font=master.font(14)
        )
        language_label.grid(row=0, column=0, padx=10)

        self.language_var = tk.StringVar(value=LANGUAGE_LABELS[master.language])

        language_box = ttk.Combobox(
            language_frame,
            textvariable=self.language_var,
            values=list(LANGUAGE_LABELS.values()),
            state="readonly",
            width=20
        )
        language_box.grid(row=0, column=1, padx=10)

        font_frame = tk.Frame(self)
        font_frame.pack(pady=20)

        font_label = tk.Label(
            font_frame,
            text=master.t("font_scale"),
            font=master.font(14)
        )
        font_label.grid(row=0, column=0, padx=10)

        self.font_scale_var = tk.DoubleVar(value=master.font_scale)

        font_scale = tk.Scale(
            font_frame,
            from_=0.85,
            to=1.35,
            resolution=0.05,
            orient="horizontal",
            variable=self.font_scale_var,
            length=220
        )
        font_scale.grid(row=0, column=1, padx=10)

        apply_button = tk.Button(
            self,
            text=master.t("apply_settings"),
            width=25,
            height=2,
            command=self.apply_settings
        )
        apply_button.pack(pady=20)

        back_button = tk.Button(
            self,
            text=master.t("back"),
            width=25,
            height=2,
            command=master.show_start_screen
        )
        back_button.pack(pady=20)

    def apply_settings(self):
        selected_resolution = self.resolution_var.get()
        selected_language = language_code_from_label(self.language_var.get())
        selected_font_scale = self.font_scale_var.get()

        self.master.geometry(selected_resolution)
        self.master.font_scale = selected_font_scale
        self.master.set_language(selected_language)

        messagebox.showinfo(
            self.master.t("settings_updated"),
            self.master.t(
                "settings_updated_detail",
                resolution=selected_resolution,
                language=LANGUAGE_LABELS[selected_language],
                font_scale=selected_font_scale * 100
            )
        )

        self.master.show_settings_screen()


class GameScreen(tk.Frame):
    # Main gameplay screen containing company info, actions, and turn log.
    def __init__(self, master):
        super().__init__(master)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.game_state = getattr(master, "game_state", None)
        if self.game_state is not None:
            self.game_state.language = master.language

        title = tk.Label(
            self,
            text=master.t("app_title"),
            font=master.font(26, "bold")
        )
        title.grid(row=0, column=0, pady=(12, 6), sticky="ew")

        self.menu_button = tk.Menubutton(
            self,
            text=master.t("menu"),
            relief="raised",
            width=10
        )
        self.menu = tk.Menu(self.menu_button, tearoff=0)
        self.menu.add_command(label=master.t("save_game"), command=self.save_game)
        self.menu.add_command(label=master.t("load_game"), command=master.show_load_game_screen)
        self.menu.add_command(label=master.t("settings"), command=master.show_settings_screen)
        self.menu.add_separator()
        self.menu.add_command(label=master.t("back_to_main_menu"), command=master.show_start_screen)
        self.menu_button.config(menu=self.menu)
        self.menu_button.grid(row=0, column=0, sticky="w", padx=18, pady=(12, 6))

        if self.game_state is None:
            warning_label = tk.Label(
                self,
                text=master.t("no_game_state"),
                font=master.font(14)
            )
            warning_label.grid(row=1, column=0, pady=20)

            back_button = tk.Button(
                self,
                text=master.t("back_to_main_menu"),
                width=20,
                height=2,
                command=master.show_start_screen
            )
            back_button.grid(row=2, column=0, pady=20)
            return

        self.top_info_label = tk.Label(
            self,
            text=self.get_top_info_text(),
            font=master.font(12)
        )
        self.top_info_label.grid(row=1, column=0, pady=(0, 8), sticky="ew")

        self.main_area = tk.Frame(self)
        self.main_area.grid(row=2, column=0, sticky="nsew", padx=25, pady=(0, 8))
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(1, weight=0)

        self.left_panel = tk.LabelFrame(
            self.main_area,
            text=master.t("company_information"),
            font=master.font(12, "bold"),
            padx=15,
            pady=15
        )
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self.right_panel = tk.LabelFrame(
            self.main_area,
            text=master.t("player_actions"),
            font=master.font(12, "bold"),
            padx=15,
            pady=15
        )
        self.right_panel.grid(row=0, column=1, sticky="ns", padx=(10, 0))
        self.right_panel.grid_rowconfigure(0, weight=1)
        self.right_panel.grid_columnconfigure(0, weight=1)

        self.action_canvas = tk.Canvas(self.right_panel, width=250, highlightthickness=0)
        self.action_scrollbar = tk.Scrollbar(self.right_panel, orient="vertical", command=self.action_canvas.yview)
        self.action_content = tk.Frame(self.action_canvas)
        self.action_window = self.action_canvas.create_window((0, 0), window=self.action_content, anchor="nw")
        self.action_canvas.configure(yscrollcommand=self.action_scrollbar.set)
        self.action_canvas.grid(row=0, column=0, sticky="nsew")
        self.action_scrollbar.grid(row=0, column=1, sticky="ns")
        self.action_content.bind("<Configure>", self.update_action_scroll_region)
        self.action_canvas.bind("<Configure>", self.update_action_canvas_width)
        self.collapsed_factories = set()

        self.build_company_display()
        self.build_action_panel()
        self.build_log_panel()

    def update_action_scroll_region(self, event=None):
        self.action_canvas.configure(scrollregion=self.action_canvas.bbox("all"))

    def update_action_canvas_width(self, event):
        self.action_canvas.itemconfigure(self.action_window, width=event.width)

    def get_top_info_text(self):
        return self.master.t(
            "top_info",
            turn=self.game_state.turn,
            max_turns=(
                self.game_state.max_turns
                if self.game_state.max_turns is not None
                else self.master.t("infinite_turns")
            ),
            scenario=display_option(self.game_state.scenario, self.master.language),
            difficulty=display_option(self.game_state.difficulty, self.master.language),
            demand=self.game_state.market.current_demand,
            summary=self.game_state.market.get_market_summary(self.master.language)
        )

    def on_tab_changed(self, event):
        self.build_action_panel()
        self.after_idle(self.master.force_redraw)

    def get_selected_company(self):
        if self.game_state.show_ai_stats and hasattr(self, "company_tabs"):
            selected_tab = self.company_tabs.select()
            selected_name = self.company_tabs.tab(selected_tab, "text")

            for company in self.game_state.get_all_companies():
                if company.name == selected_name:
                    return company

        return self.game_state.player

    def build_company_display(self):
        if self.game_state.show_ai_stats:
            self.company_tabs = ttk.Notebook(self.left_panel)
            self.company_tabs.pack(fill="both", expand=True)

            self.company_status_frames = {}

            for company in self.game_state.get_all_companies():
                tab = tk.Frame(self.company_tabs, bg="#f0f0f0")

                self.render_company_status(tab, company)

                self.company_tabs.add(tab, text=company.name)
                self.company_status_frames[company.name] = tab

            self.company_tabs.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        else:
            self.player_status_frame = tk.Frame(self.left_panel, bg="#f0f0f0")
            self.player_status_frame.pack(fill="both", expand=True, padx=12, pady=12)
            self.render_company_status(self.player_status_frame, self.game_state.player)

    def render_company_status(self, parent, company):
        for child in parent.winfo_children():
            child.destroy()

        for section_index, (section_title, items) in enumerate(company.get_status_sections(self.master.language)):
            section = tk.LabelFrame(
                parent,
                text=section_title,
                font=self.master.font(11, "bold"),
                padx=8,
                pady=6,
                bg="#f0f0f0"
            )
            section.grid(
                row=section_index // 2,
                column=section_index % 2,
                sticky="nsew",
                padx=6,
                pady=6
            )
            parent.grid_columnconfigure(section_index % 2, weight=1)

            for item_index, (label, value) in enumerate(items):
                row = item_index // 2
                column = (item_index % 2) * 2
                tk.Label(
                    section,
                    text=f"{label}:",
                    font=self.master.font(10, "bold"),
                    bg="#f0f0f0",
                    anchor="w"
                ).grid(row=row, column=column, sticky="w", padx=(0, 4), pady=2)
                tk.Label(
                    section,
                    text=value,
                    font=self.master.font(10),
                    bg="#f0f0f0",
                    anchor="w",
                    wraplength=170
                ).grid(row=row, column=column + 1, sticky="w", padx=(0, 12), pady=2)

    def build_action_panel(self):
        for child in self.action_content.winfo_children():
            child.destroy()

        parent = self.action_content
        selected_company = self.get_selected_company()

        if not selected_company.is_player:
            self.build_ai_negotiation_panel(parent, selected_company)
            self.update_action_scroll_region()
            return

        production_label = tk.Label(
            parent,
            text=self.master.t("production_quantity")
        )
        production_label.pack(anchor="w", pady=5)

        self.production_entry = tk.Entry(
            parent,
            bg="white",
            fg="black",
            insertbackground="black"
        )
        self.production_entry.pack(anchor="w", pady=5)
        self.production_entry.insert(0, str(int(self.game_state.player.get_production_capacity() * 0.7)))

        price_label = tk.Label(
            parent,
            text=self.master.t("selling_price")
        )
        price_label.pack(anchor="w", pady=5)

        self.price_entry = tk.Entry(
            parent,
            bg="white",
            fg="black",
            insertbackground="black"
        )
        self.price_entry.pack(anchor="w", pady=5)

        self.price_entry.insert(0, str(self.game_state.player.price))

        end_turn_button = tk.Button(
            parent,
            text=self.master.t("end_turn"),
            width=22,
            height=2,
            command=self.end_turn
        )
        end_turn_button.pack(anchor="w", pady=20)

        investment_label = tk.Label(
            parent,
            text=self.master.t("long_term_actions")
        )
        investment_label.pack(anchor="w", pady=(18, 5))

        science_button = tk.Button(
            parent,
            text=self.master.t("science_technology"),
            width=22,
            command=lambda: self.open_technology_tree(self.game_state.player, "own")
        )
        science_button.pack(anchor="w", pady=3)

        factory_button = tk.Button(
            parent,
            text=self.master.t("factory"),
            width=22,
            command=self.open_factory_panel
        )
        factory_button.pack(anchor="w", pady=3)

        contracts_button = tk.Button(
            parent,
            text=self.master.t("contracts"),
            width=22,
            command=self.open_contract_panel
        )
        contracts_button.pack(anchor="w", pady=3)

        storage_button = tk.Button(
            parent,
            text=f"{self.master.t('expand_storage')} ($2000.00)",
            width=22,
            command=self.expand_storage
        )
        storage_button.pack(anchor="w", pady=3)

        marketing_button = tk.Button(
            parent,
            text=f"{self.master.t('marketing_campaign')} ($1200.00)",
            width=22,
            command=self.run_marketing_campaign
        )
        marketing_button.pack(anchor="w", pady=3)

        finance_label = tk.Label(
            parent,
            text=self.master.t("finance")
        )
        finance_label.pack(anchor="w", pady=(14, 5))

        chart_button = tk.Button(
            parent,
            text=self.master.t("finance_chart"),
            width=22,
            command=self.open_finance_chart
        )
        chart_button.pack(anchor="w", pady=3)

        restructure_button = tk.Button(
            parent,
            text=self.master.t("emergency_restructure"),
            width=22,
            command=self.emergency_restructure
        )
        restructure_button.pack(anchor="w", pady=3)

        self.update_action_scroll_region()

    def build_ai_negotiation_panel(self, parent, company):
        technology_button = tk.Button(
            parent,
            text=self.master.t("science_technology"),
            width=22,
            command=lambda: self.open_technology_tree(company, "foreign")
        )
        technology_button.pack(anchor="w", pady=(0, 12))

        offer_label = tk.Label(
            parent,
            text=self.master.t("acquisition_offer")
        )
        offer_label.pack(anchor="w", pady=5)

        self.acquisition_offer_entry = tk.Entry(
            parent,
            bg="white",
            fg="black",
            insertbackground="black"
        )
        self.acquisition_offer_entry.pack(anchor="w", pady=5)
        self.acquisition_offer_entry.insert(0, str(company.get_acquisition_value()))

        negotiate_button = tk.Button(
            parent,
            text=self.master.t("acquire_competitor"),
            width=22,
            height=2,
            command=lambda: self.negotiate_acquisition(company)
        )
        negotiate_button.pack(anchor="w", pady=12)

    def build_back_to_actions_button(self, parent):
        button = tk.Button(
            parent,
            text=self.master.t("back"),
            width=22,
            command=self.build_action_panel
        )
        button.pack(anchor="w", pady=(0, 12))

    def open_finance_chart(self):
        for child in self.action_content.winfo_children():
            child.destroy()

        parent = self.action_content
        self.build_back_to_actions_button(parent)

        tk.Label(
            parent,
            text=self.master.t("finance_chart"),
            font=self.master.font(12, "bold")
        ).pack(anchor="w", pady=(0, 8))

        canvas_width = 225
        canvas_height = 190
        canvas = tk.Canvas(
            parent,
            width=canvas_width,
            height=canvas_height,
            bg="white",
            highlightthickness=1,
            highlightbackground="#b8c2cc"
        )
        canvas.pack(anchor="w", pady=(0, 8))

        player = self.game_state.player
        net_history = player.get_finance_position_history()
        credit_floor_history = [-value for value in player.credit_limit_history]
        self.draw_finance_chart(canvas, canvas_width, canvas_height, net_history, credit_floor_history)

        legend = tk.Frame(parent)
        legend.pack(anchor="w", fill="x")
        legend_items = [
            (self.master.t("chart_cash"), "#1f7a4d"),
            (self.master.t("chart_debt"), "#b23a48"),
            (self.master.t("chart_credit_limit"), "#2f5fb3")
        ]
        for label, color in legend_items:
            row = tk.Frame(legend)
            row.pack(anchor="w", pady=1)
            swatch = tk.Canvas(row, width=14, height=10, highlightthickness=0)
            swatch.create_rectangle(0, 2, 14, 8, fill=color, outline=color)
            swatch.pack(side="left", padx=(0, 5))
            tk.Label(row, text=label).pack(side="left")

        self.update_action_scroll_region()

    def draw_finance_chart(self, canvas, width, height, net_history, credit_floor_history):
        left = 32
        right = width - 10
        top = 14
        bottom = height - 24
        plot_width = right - left
        plot_height = bottom - top
        net_history = net_history[-24:]
        credit_floor_history = credit_floor_history[-24:]

        values = net_history + credit_floor_history

        if len(values) < 2:
            canvas.create_text(
                width / 2,
                height / 2,
                text=self.master.t("chart_no_data"),
                fill="#555"
            )
            return

        minimum = min(0, min(values))
        maximum = max(values)
        if maximum == minimum:
            maximum = minimum + 1

        def point(index, value, count):
            x = left + (plot_width * index / max(1, count - 1))
            y = bottom - ((value - minimum) / (maximum - minimum) * plot_height)
            return x, y

        canvas.create_line(left, top, left, bottom, fill="#777")
        canvas.create_line(left, bottom, right, bottom, fill="#777")
        if minimum < 0 < maximum:
            zero_y = point(0, 0, 2)[1]
            canvas.create_line(left, zero_y, right, zero_y, fill="#999", dash=(3, 3))
        canvas.create_text(left - 4, top, text=f"{maximum:.0f}", anchor="e", fill="#555", font=self.master.font(8))
        canvas.create_text(left - 4, bottom, text=f"{minimum:.0f}", anchor="e", fill="#555", font=self.master.font(8))

        if len(credit_floor_history) >= 2:
            credit_points = []
            for index, value in enumerate(credit_floor_history):
                credit_points.extend(point(index, value, len(credit_floor_history)))
            canvas.create_line(*credit_points, fill="#2f5fb3", width=2)

        if len(net_history) < 2:
            return

        for index in range(1, len(net_history)):
            previous_point = point(index - 1, net_history[index - 1], len(net_history))
            current_point = point(index, net_history[index], len(net_history))
            segment_color = "#1f7a4d" if (net_history[index - 1] + net_history[index]) / 2 >= 0 else "#b23a48"
            canvas.create_line(
                previous_point[0],
                previous_point[1],
                current_point[0],
                current_point[1],
                fill=segment_color,
                width=2
            )

    def open_contract_panel(self):
        for child in self.action_content.winfo_children():
            child.destroy()

        parent = self.action_content
        self.build_back_to_actions_button(parent)

        tk.Label(
            parent,
            text=self.master.t("contracts"),
            font=self.master.font(12, "bold")
        ).pack(anchor="w", pady=(0, 8))

        active_player_contracts = [
            contract for contract in self.game_state.contracts
            if contract.get("holder") == self.game_state.player.name
        ]
        tk.Label(parent, text=self.master.t("active_contracts"), font=self.master.font(10, "bold")).pack(anchor="w")

        if active_player_contracts:
            for contract in active_player_contracts:
                tk.Label(
                    parent,
                    text=self.format_contract_detail(contract, include_holder=True),
                    justify="left",
                    anchor="w",
                    wraplength=220
                ).pack(fill="x", anchor="w", pady=(3, 8))
        else:
            tk.Label(parent, text=self.master.t("no_active_contracts"), wraplength=220).pack(anchor="w", pady=(3, 8))

        tk.Label(parent, text=self.master.t("available_contracts"), font=self.master.font(10, "bold")).pack(anchor="w", pady=(8, 3))
        available_contracts = [
            contract for contract in self.game_state.contracts
            if contract.get("holder") is None
        ]

        if not available_contracts:
            tk.Label(parent, text=self.master.t("no_available_contracts"), wraplength=220).pack(anchor="w")

        for contract in available_contracts:
            frame = tk.LabelFrame(
                parent,
                text=self.game_state.get_contract_name(contract),
                padx=8,
                pady=6
            )
            frame.pack(fill="x", pady=6)

            tk.Label(
                frame,
                text=self.format_contract_detail(contract, include_holder=False),
                justify="left",
                anchor="w",
                wraplength=205
            ).pack(fill="x")

            tk.Label(frame, text=self.master.t("contract_bid_price")).pack(anchor="w", pady=(6, 2))
            bid_entry = tk.Entry(frame, width=12)
            bid_entry.pack(anchor="w")
            bid_entry.insert(0, f"{contract['unit_price']:.2f}")

            tk.Button(
                frame,
                text=self.master.t("compete_contract"),
                command=lambda item=contract, entry=bid_entry: self.compete_contract_from_panel(item, entry)
            ).pack(anchor="w", pady=(6, 0))

        self.update_action_scroll_region()

    def format_contract_detail(self, contract, include_holder=False):
        template = CONTRACT_TEMPLATES[contract["type"]]
        lines = [
            template["description"][self.master.language],
            f"{self.master.t('contract_units')}: {contract['units_per_turn']}",
            f"{self.master.t('contract_price')}: ${contract['unit_price']:.2f}",
            f"{self.master.t('contract_duration')}: {contract['remaining_turns']}/{contract['duration']}",
            f"{self.master.t('contract_quality')}: {contract['quality_requirement']}",
            f"{self.master.t('contract_reputation')}: {contract['reputation_requirement']}"
        ]

        if include_holder:
            lines.append(f"{self.master.t('contract_holder')}: {contract.get('holder') or '-'}")

        return "\n".join(lines)

    def compete_contract_from_panel(self, contract, bid_entry):
        try:
            bid_price = float(bid_entry.get())
            if bid_price <= 0:
                raise ValueError("Bid price must be positive.")
        except ValueError as error:
            messagebox.showerror(self.master.t("invalid_input_title"), str(error))
            return

        def action():
            return self.master.t(
                "player_action_prefix",
                message=self.game_state.compete_for_contract(contract["id"], bid_price)
            )

        self.run_player_action(self.master.t("contracts"), action)
        self.open_contract_panel()

    def open_technology_tree(self, company, mode):
        for child in self.action_content.winfo_children():
            child.destroy()

        parent = self.action_content
        self.build_back_to_actions_button(parent)

        title = tk.Label(
            parent,
            text=f"{self.master.t('technology_tree')} - {company.name}",
            font=self.master.font(12, "bold"),
            wraplength=220,
            justify="left"
        )
        title.pack(anchor="w", pady=(0, 8))

        for technology_id, technology in TECHNOLOGIES.items():
            frame = tk.LabelFrame(
                parent,
                text=technology["name"][self.master.language],
                padx=8,
                pady=6
            )
            frame.pack(fill="x", pady=6)

            prereq_text = ", ".join(
                TECHNOLOGIES[prerequisite]["name"][self.master.language]
                for prerequisite in technology["prerequisites"]
            ) or "-"

            active_project = next(
                (
                    project for project in company.active_research
                    if project["technology_id"] == technology_id
                ),
                None
            )

            if technology_id in company.known_technologies:
                status = self.master.t("known_technology")
            elif active_project:
                status = self.master.t("researching_technology", turns=active_project["remaining_turns"])
            elif company.can_research_technology(technology_id):
                status = self.master.t("start_research", cost=technology["cost"])
            else:
                status = self.master.t("locked_technology")

            detail = (
                f"{technology['description'][self.master.language]}\n"
                f"{self.master.t('tech_cost')}: ${technology['cost']:.2f}\n"
                f"{self.master.t('tech_turns')}: {technology['turns']}\n"
                f"{self.master.t('tech_prerequisites')}: {prereq_text}\n"
                f"{self.master.t('tech_status')}: {status}"
            )
            tk.Label(frame, text=detail, justify="left", anchor="w", wraplength=205).pack(fill="x")

            if mode == "own" and company.can_research_technology(technology_id):
                tk.Button(
                    frame,
                    text=self.master.t("start_research", cost=technology["cost"]),
                    command=lambda tech_id=technology_id: self.start_research_from_panel(tech_id)
                ).pack(anchor="w", pady=(6, 0))

            if mode == "foreign" and technology_id in company.known_technologies:
                if technology_id not in self.game_state.player.known_technologies:
                    offer_entry = tk.Entry(frame, width=14)
                    offer_entry.pack(anchor="w", pady=(6, 2))
                    offer_entry.insert(0, str(int(technology["cost"] * 2.5)))

                    tk.Button(
                        frame,
                        text=self.master.t("buy_technology"),
                        command=lambda tech_id=technology_id, entry=offer_entry, seller=company: self.buy_technology_from_panel(seller, tech_id, entry)
                    ).pack(anchor="w")

        self.update_action_scroll_region()

    def start_research_from_panel(self, technology_id):
        try:
            cost = self.game_state.player.start_technology_research(technology_id)
        except ValueError as error:
            messagebox.showerror(self.master.t("turn_error"), str(error))
            return

        self.add_log(
            self.master.t(
                "player_action_prefix",
                message=self.master.t(
                    "technology_research_started",
                    technology=TECHNOLOGIES[technology_id]["name"][self.master.language],
                    cost=cost
                )
            )
        )
        self.refresh_display()
        self.open_technology_tree(self.game_state.player, "own")

    def buy_technology_from_panel(self, seller, technology_id, offer_entry):
        try:
            offer = float(offer_entry.get())
            if offer <= 0:
                raise ValueError("Offer must be positive.")
        except ValueError as error:
            messagebox.showerror(self.master.t("invalid_input_title"), str(error))
            return

        try:
            message = self.game_state.negotiate_technology_purchase(seller.name, technology_id, offer)
        except ValueError as error:
            messagebox.showerror(self.master.t("turn_error"), str(error))
            return

        self.add_log(self.master.t("player_action_prefix", message=message))
        self.refresh_display()
        self.open_technology_tree(seller, "foreign")

    def open_factory_panel(self):
        for child in self.action_content.winfo_children():
            child.destroy()

        parent = self.action_content
        player = self.game_state.player
        language = self.master.language
        self.build_back_to_actions_button(parent)

        title = tk.Label(parent, text=self.master.t("factory"), font=self.master.font(12, "bold"))
        title.pack(anchor="w", pady=(0, 8))

        tk.Label(
            parent,
            text=(
                f"{self.master.t('factory_slots')}: "
                f"{player.get_used_factory_slots()}/{player.get_factory_slots()}\n"
                f"{self.master.t('unassigned_workers')}: {player.get_unassigned_workers()}"
            ),
            justify="left",
            anchor="w",
            wraplength=220
        ).pack(anchor="w", fill="x", pady=(0, 10))

        build_factory_cost = player.get_build_factory_cost()
        tk.Button(
            parent,
            text=f"{self.master.t('build_factory')} (${build_factory_cost:.2f})",
            width=22,
            command=self.build_factory
        ).pack(anchor="w", pady=3)

        lease_factory_cost = player.get_lease_factory_cost()
        tk.Button(
            parent,
            text=f"{self.master.t('lease_factory')} (${lease_factory_cost:.2f})",
            width=22,
            command=self.lease_factory
        ).pack(anchor="w", pady=3)

        workforce_frame = tk.LabelFrame(parent, text=self.master.t("worker_count"), padx=8, pady=6)
        workforce_frame.pack(fill="x", pady=8)
        worker_count_entry = tk.Entry(workforce_frame, width=10)
        worker_count_entry.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        worker_count_entry.insert(0, "5")
        tk.Button(
            workforce_frame,
            text=f"{self.master.t('hire_workers')} ($700.00/worker)",
            command=lambda entry=worker_count_entry: self.hire_workers(entry)
        ).grid(row=1, column=0, sticky="w", padx=(0, 5), pady=2)
        tk.Button(
            workforce_frame,
            text=self.master.t("fire_workers"),
            command=lambda entry=worker_count_entry: self.fire_workers(entry)
        ).grid(row=1, column=1, sticky="w", pady=2)

        for factory_index, factory in enumerate(player.factory_buildings):
            line_indices = player.get_factory_line_indices(factory_index)
            factory_frame = tk.LabelFrame(
                parent,
                text=f"{factory['name']} ({len(line_indices)}/{factory['slots']})",
                padx=8,
                pady=6
            )
            factory_frame.pack(fill="x", pady=8)

            owned = factory.get("owned", True)
            factory_type = self.master.t("owned_factory") if owned else self.master.t("leased_factory")
            expansion_limit = player.get_factory_expansion_limit(factory_index)
            factory_info = (
                f"{self.master.t('factory_type')}: {factory_type}\n"
                f"{self.master.t('factory_expansions')}: "
                f"{factory.get('expansions', 0)}/{expansion_limit}"
            )
            if not owned:
                factory_info += f"\n{self.master.t('factory_rent')}: ${factory.get('rent', 0):.2f}"
            tk.Label(factory_frame, text=factory_info, justify="left", anchor="w").pack(anchor="w", pady=(0, 6))

            toggle_key = "expand_view" if factory_index in self.collapsed_factories else "collapse_factory"
            tk.Button(
                factory_frame,
                text=self.master.t(toggle_key),
                command=lambda index=factory_index: self.toggle_factory_panel(index)
            ).pack(anchor="w", pady=(0, 6))

            if factory_index in self.collapsed_factories:
                continue

            factory_action_frame = tk.Frame(factory_frame)
            factory_action_frame.pack(fill="x", pady=(0, 6))
            line_button_state = "normal" if player.get_factory_free_slots(factory_index) > 0 else "disabled"
            line_cost = 5200 + player.production_lines * 1400
            tk.Button(
                factory_action_frame,
                text=f"{self.master.t('build_line_here')} (${line_cost:.2f})",
                command=lambda index=factory_index: self.buy_production_line(index),
                state=line_button_state
            ).grid(row=0, column=0, sticky="w", pady=2)

            if owned and factory.get("expansions", 0) < expansion_limit:
                factory_expand_cost = player.get_factory_expand_cost(factory_index)
                expand_text = f"{self.master.t('expand_factory')} (${factory_expand_cost:.2f})"
                expand_state = "normal"
            elif owned:
                expand_text = self.master.t("expansion_limit_reached")
                expand_state = "disabled"
            else:
                expand_text = self.master.t("cannot_expand_leased")
                expand_state = "disabled"

            tk.Button(
                factory_action_frame,
                text=expand_text,
                command=lambda index=factory_index: self.expand_factory(index),
                state=expand_state
            ).grid(row=1, column=0, sticky="w", pady=2)

            batch_frame = tk.Frame(factory_frame)
            batch_frame.pack(fill="x", pady=(0, 6))
            batch_entry = tk.Entry(batch_frame, width=8)
            batch_entry.grid(row=0, column=0, sticky="w", padx=(0, 4), pady=2)
            batch_entry.insert(0, "1")
            tk.Button(
                batch_frame,
                text=self.master.t("batch_add_workers"),
                command=lambda index=factory_index, entry=batch_entry: self.adjust_factory_workers(index, entry, 1)
            ).grid(row=1, column=0, sticky="w", pady=2)
            tk.Button(
                batch_frame,
                text=self.master.t("batch_remove_workers"),
                command=lambda index=factory_index, entry=batch_entry: self.adjust_factory_workers(index, entry, -1)
            ).grid(row=2, column=0, sticky="w", pady=2)

            upgrade_cost, upgrade_count, target_method = player.get_factory_upgrade_plan(factory_index)
            upgrade_text = (
                f"{self.master.t('batch_upgrade_lines')} "
                f"({upgrade_count}, ${upgrade_cost:.2f})"
                if upgrade_count
                else self.master.t("already_best_method")
            )
            tk.Button(
                batch_frame,
                text=upgrade_text,
                command=lambda index=factory_index: self.upgrade_factory_lines(index),
                state=("normal" if upgrade_count else "disabled")
            ).grid(row=3, column=0, sticky="w", pady=2)

            for line_index in line_indices:
                line = player.production_line_details[line_index]
                line_frame = tk.LabelFrame(
                    factory_frame,
                    text=f"{self.master.t('production_line')} {line_index + 1}",
                    padx=8,
                    pady=6
                )
                line_frame.pack(fill="x", pady=5)

                status = self.master.t("line_active") if line["active"] else self.master.t("line_inactive")
                min_workers, optimal_workers, max_workers = player.get_line_worker_targets(line)
                method_name = TECHNOLOGIES[line["method"]]["name"][language]
                info = (
                    f"{self.master.t('tech_status')}: {status}\n"
                    f"{self.master.t('production_method')}: {method_name}\n"
                    f"{self.master.t('assigned_workers')}: {line['workers']} "
                    f"({min_workers}/{optimal_workers}/{max_workers})"
                )
                tk.Label(line_frame, text=info, justify="left", anchor="w").pack(anchor="w")

                worker_entry = tk.Entry(line_frame, width=10)
                worker_entry.pack(anchor="w", pady=(6, 2))
                worker_entry.insert(0, str(line["workers"]))

                tk.Button(
                    line_frame,
                    text=self.master.t("assign_workers"),
                    command=lambda index=line_index, entry=worker_entry: self.assign_workers(index, entry)
                ).pack(anchor="w", pady=2)

                worker_delta_entry = tk.Entry(line_frame, width=10)
                worker_delta_entry.pack(anchor="w", pady=(6, 2))
                worker_delta_entry.insert(0, "1")

                tk.Button(
                    line_frame,
                    text=self.master.t("add_workers"),
                    command=lambda index=line_index, entry=worker_delta_entry: self.adjust_line_workers(index, entry, 1)
                ).pack(anchor="w", pady=2)
                tk.Button(
                    line_frame,
                    text=self.master.t("remove_workers"),
                    command=lambda index=line_index, entry=worker_delta_entry: self.adjust_line_workers(index, entry, -1)
                ).pack(anchor="w", pady=2)

                active_toggle_key = "stop_line" if line["active"] else "start_line"
                tk.Button(
                    line_frame,
                    text=self.master.t(active_toggle_key),
                    command=lambda index=line_index, active=not line["active"]: self.toggle_line(index, active)
                ).pack(anchor="w", pady=2)

                target_method = player.get_best_available_production_method()
                if target_method != line["method"]:
                    line_upgrade_cost = player.get_line_upgrade_cost(line["method"], target_method)
                    upgrade_line_text = self.master.t(
                        "upgrade_to_method",
                        method=TECHNOLOGIES[target_method]["name"][language],
                        cost=line_upgrade_cost
                    )
                    upgrade_state = "normal"
                else:
                    upgrade_line_text = self.master.t("already_best_method")
                    upgrade_state = "disabled"

                tk.Button(
                    line_frame,
                    text=upgrade_line_text,
                    command=lambda index=line_index: self.upgrade_line(index),
                    state=upgrade_state
                ).pack(anchor="w", pady=2)

        self.update_action_scroll_region()

    def build_log_panel(self):
        self.log_panel = tk.LabelFrame(
            self,
            text=self.master.t("turn_log"),
            font=self.master.font(12, "bold"),
            padx=10,
            pady=10
        )
        self.log_panel.grid(row=3, column=0, sticky="ew", padx=35, pady=(0, 10))
        self.log_panel.grid_columnconfigure(0, weight=1)

        self.log_text = tk.Text(
            self.log_panel,
            height=7,
            font=self.master.font(10),
            bg="white",
            fg="black",
            insertbackground="black",
            wrap="word"
        )
        self.log_text.grid(row=0, column=0, sticky="ew")

        scrollbar = tk.Scrollbar(
            self.log_panel,
            command=self.log_text.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.log_text.config(yscrollcommand=scrollbar.set)

        self.log_text.insert(
            tk.END,
            self.master.t("game_started")
        )

        self.log_text.config(state="disabled")

    def add_log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, "\n" + message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def refresh_display(self):
        self.top_info_label.config(text=self.get_top_info_text())

        if self.game_state.show_ai_stats:
            for company in self.game_state.get_all_companies():
                self.render_company_status(self.company_status_frames[company.name], company)
        else:
            self.render_company_status(self.player_status_frame, self.game_state.player)

        self.after_idle(self.master.force_redraw)

    def run_player_action(self, action_name, action):
        try:
            message = action()
        except ValueError as error:
            messagebox.showerror(action_name, str(error))
            return

        self.refresh_display()
        self.add_log(message)

    def buy_production_line(self, factory_index=None):
        def action():
            target_factory_index = (
                self.game_state.player.get_default_factory_index()
                if factory_index is None
                else factory_index
            )
            factory = self.game_state.player.factory_buildings[target_factory_index]
            cost = self.game_state.player.buy_production_line(target_factory_index)
            return self.master.t(
                "player_action_prefix",
                message=self.master.t("production_line_log", cost=cost, factory=factory["name"])
            )

        self.run_player_action(self.master.t("buy_production_line"), action)
        self.open_factory_panel()

    def build_factory(self):
        def action():
            cost, factory_name = self.game_state.player.build_factory()
            return self.master.t(
                "player_action_prefix",
                message=self.master.t("factory_built_log", cost=cost, factory=factory_name)
            )

        self.run_player_action(self.master.t("build_factory"), action)
        self.open_factory_panel()

    def lease_factory(self):
        def action():
            cost, factory_name = self.game_state.player.lease_factory()
            return self.master.t(
                "player_action_prefix",
                message=self.master.t("factory_leased_log", cost=cost, factory=factory_name)
            )

        self.run_player_action(self.master.t("lease_factory"), action)
        self.open_factory_panel()

    def parse_worker_count(self, worker_entry):
        count = int(worker_entry.get())
        if count <= 0:
            raise ValueError("Worker count must be positive.")
        return count

    def hire_workers(self, worker_entry):
        def action():
            count = self.parse_worker_count(worker_entry)
            cost = self.game_state.player.hire_workers(count)
            return self.master.t(
                "player_action_prefix",
                message=self.master.t("hire_workers_log", count=count, cost=cost)
            )

        self.run_player_action(self.master.t("hire_workers"), action)
        self.open_factory_panel()

    def fire_workers(self, worker_entry):
        def action():
            count = self.parse_worker_count(worker_entry)
            self.game_state.player.fire_workers(count)
            return self.master.t(
                "player_action_prefix",
                message=self.master.t("fire_workers_log", count=count)
            )

        self.run_player_action(self.master.t("fire_workers"), action)
        self.open_factory_panel()

    def assign_workers(self, line_index, worker_entry):
        try:
            workers = int(worker_entry.get())
            self.game_state.player.assign_workers_to_line(line_index, workers)
        except ValueError as error:
            messagebox.showerror(self.master.t("invalid_input_title"), str(error))
            return

        self.refresh_display()
        self.open_factory_panel()

    def adjust_line_workers(self, line_index, worker_entry, direction):
        try:
            count = self.parse_worker_count(worker_entry)
            delta = count * direction
            self.game_state.player.adjust_workers_on_line(line_index, delta)
        except ValueError as error:
            messagebox.showerror(self.master.t("invalid_input_title"), str(error))
            return

        self.add_log(
            self.master.t(
                "player_action_prefix",
                message=self.master.t("workers_changed_log", delta=delta)
            )
        )
        self.refresh_display()
        self.open_factory_panel()

    def adjust_factory_workers(self, factory_index, worker_entry, direction):
        try:
            count = self.parse_worker_count(worker_entry)
            delta = count * direction
            self.game_state.player.adjust_workers_in_factory(factory_index, delta)
        except ValueError as error:
            messagebox.showerror(self.master.t("invalid_input_title"), str(error))
            return

        factory = self.game_state.player.factory_buildings[factory_index]
        self.add_log(
            self.master.t(
                "player_action_prefix",
                message=self.master.t(
                    "batch_workers_changed_log",
                    delta=delta,
                    factory=factory["name"]
                )
            )
        )
        self.refresh_display()
        self.open_factory_panel()

    def toggle_factory_panel(self, factory_index):
        if factory_index in self.collapsed_factories:
            self.collapsed_factories.remove(factory_index)
        else:
            self.collapsed_factories.add(factory_index)

        self.open_factory_panel()

    def toggle_line(self, line_index, active):
        self.game_state.player.set_production_line_active(line_index, active)
        self.refresh_display()
        self.open_factory_panel()

    def upgrade_line(self, line_index):
        def action():
            cost, method = self.game_state.player.upgrade_production_line(line_index)
            return self.master.t(
                "player_action_prefix",
                message=self.master.t(
                    "upgrade_line_log",
                    cost=cost,
                    method=TECHNOLOGIES[method]["name"][self.master.language]
                )
            )

        self.run_player_action(self.master.t("upgrade_line"), action)
        self.open_factory_panel()

    def upgrade_factory_lines(self, factory_index):
        def action():
            cost, count, method = self.game_state.player.upgrade_factory_lines(factory_index)
            return self.master.t(
                "player_action_prefix",
                message=self.master.t(
                    "batch_upgrade_lines_log",
                    cost=cost,
                    count=count,
                    method=TECHNOLOGIES[method]["name"][self.master.language]
                )
            )

        self.run_player_action(self.master.t("batch_upgrade_lines"), action)
        self.open_factory_panel()

    def expand_factory(self, factory_index):
        def action():
            factory = self.game_state.player.factory_buildings[factory_index]
            cost = self.game_state.player.expand_factory(factory_index)
            return self.master.t(
                "player_action_prefix",
                message=self.master.t("factory_expanded_log", cost=cost, factory=factory["name"])
            )

        self.run_player_action(self.master.t("expand_factory"), action)
        self.open_factory_panel()

    def expand_storage(self):
        def action():
            cost = self.game_state.player.expand_storage(250)
            return self.master.t(
                "player_action_prefix",
                message=self.master.t("storage_log", cost=cost)
            )

        self.run_player_action(self.master.t("expand_storage"), action)

    def run_marketing_campaign(self):
        def action():
            cost = self.game_state.player.run_marketing_campaign(1200)
            return self.master.t(
                "player_action_prefix",
                message=self.master.t("marketing_log", cost=cost)
            )

        self.run_player_action(self.master.t("marketing_campaign"), action)

    def negotiate_acquisition(self, company):
        offer = self.acquisition_offer_entry.get()

        try:
            offer = float(offer)

            if offer <= 0:
                raise ValueError("Offer must be positive.")
        except ValueError as error:
            messagebox.showerror(
                self.master.t("invalid_input_title"),
                self.master.t("invalid_input", error=error)
            )
            return

        def action():
            return self.master.t(
                "player_action_prefix",
                message=self.game_state.negotiate_acquisition(company.name, offer)
            )

        self.run_player_action(self.master.t("acquire_competitor"), action)
        self.build_action_panel()

    def emergency_restructure(self):
        def action():
            reduction = self.game_state.player.emergency_restructure()
            return self.master.t(
                "player_action_prefix",
                message=self.master.t("restructure_log", amount=reduction)
            )

        self.run_player_action(self.master.t("emergency_restructure"), action)

    def end_turn(self):
        production = self.production_entry.get()
        price = self.price_entry.get()

        try:
            production = int(production)
            price = float(price)

            if production < 0:
                raise ValueError("Production cannot be negative.")

            if price <= 0:
                raise ValueError("Price must be positive.")

        except ValueError as error:
            messagebox.showerror(
                self.master.t("invalid_input_title"),
                self.master.t("invalid_input", error=error)
            )
            return

        try:
            self.game_state.language = self.master.language
            report = self.game_state.process_turn(
                player_production=production,
                player_price=price
            )

        except ValueError as error:
            messagebox.showerror(
                self.master.t("turn_error"),
                str(error)
            )
            return

        self.refresh_display()

        self.add_log(
            self.master.t("turn_header", turn=self.game_state.turn - 1, report=report)
        )

        if self.game_state.is_game_over():
            result = self.game_state.get_game_result_text()
            messagebox.showinfo(
                self.master.t("game_over"),
                result
            )

    def save_game(self):
        try:
            save_name = save_game_state(self.game_state)
        except OSError as error:
            messagebox.showerror(self.master.t("save_failed"), str(error))
            return

        self.add_log(self.master.t("save_success", save=save_name))
        messagebox.showinfo(self.master.t("save_game"), self.master.t("save_success", save=save_name))
