from IPython.display import HTML, display, clear_output
import pandas as pd
from ipywidgets import interact, widgets, VBox, Output, GridBox, Layout, Label, ToggleButtons, HBox, Box
from IPython.display import display, clear_output


def __init__():
    pass


# Global state
if "_pivot_state" not in locals():
    _pivot_state = {
        'last_df_id': None,
        'index': [],
        'columns': None,
        'values': [],
        'aggfunc': 'sum',
        'scale_factor': 1,
        'filters': {},
        'user_selected_fields_as_filters': [],
        'last_pivot': pd.DataFrame()
    }

def interactive_pivot(df):
    global _pivot_state

    current_df_id = str(df.columns)
    if _pivot_state['last_df_id'] != current_df_id:
        _pivot_state = {
            'last_df_id': current_df_id,
            'index': [],
            'columns': None,
            'values': [],
            'aggfunc': 'sum',
            'scale_factor': 1,
            'filters': {},
            'user_selected_fields_as_filters': [],
            'last_pivot': pd.DataFrame()
        }

    df = df.copy()
   
    # Ensure unique column names
    new_col_list = []
    for col in df.columns:
        suffix = f"_{str(uuid.uuid4())[0:6]}" if col in new_col_list else ""
        new_col_list.append(col + suffix)
    df.columns = new_col_list

    categorical_columns = [] #sorted([col for col, n in df.nunique(dropna=True).items() if n <= 150])
    for col in sorted(df.columns):
        try:
            if df[col].nunique(dropna=True) <= 150:
                categorical_columns.append(col)
        except:
            pass
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(0)
        else:
            df[col] = df[col].fillna("None")

   
    numeric_columns = sorted(df.select_dtypes(include='number').columns.tolist())

    TG_FILTER = "filters"
    TG_INDEX = "rows"
    TG_VALUES = "aggregate"

    # State
    selected = {
        TG_FILTER : _pivot_state['user_selected_fields_as_filters'],
        TG_INDEX: _pivot_state['index'],
        TG_VALUES: _pivot_state['values']
    }

    # UI Elements
    role_selector = ToggleButtons(
        options=[TG_INDEX, TG_VALUES, TG_FILTER],
        value=TG_INDEX,
    )

    column_list = sorted(df.columns.tolist())

    field_selector = widgets.SelectMultiple(
        options=column_list,
        layout=Layout(width='95%'),
        rows = 14
    )

    fild_selector_filter = widgets.Text(placeholder='Field name filter...', layout=Layout(width='95%'))

    # Filtering logic
    def on_fild_selector_filter_change(change):
        text = change['new'].lower()
        if text:
            filtered = [col for col in column_list if text in col.lower()]
            field_selector.options = sorted(filtered)
        else:
            field_selector.options = sorted(column_list)

    fild_selector_filter.observe(on_fild_selector_filter_change, names='value')

    field_selector_box = VBox([fild_selector_filter, field_selector])

    filter_box = Box(layout=Layout(display='flex', flex_flow='row wrap', align_items='flex-start', gap='8px'))
    index_box = Box(layout=Layout(display='flex', flex_flow='row wrap', align_items='flex-start', gap='8px'))
    values_box = Box(layout=Layout(display='flex', flex_flow='row wrap', align_items='flex-start', gap='8px'))
   
    #GridBox()#GridBox(layout=Layout(grid_template_columns="repeat(auto-fill, minmax(120px, 1fr))", grid_gap="5px"))
    boxes = {TG_INDEX: index_box, TG_VALUES: values_box, TG_FILTER: filter_box}
   
    # Render helpers
    def render_buttons(category):
        box = boxes[category]
        buttons = []
        for col in selected[category]:
            button_and_updown = []
            btn_priority_up = widgets.Button(description="⇽", layout=Layout(width='3px'))
            def on_click_p_up(b, col=col, cat=category):
                item_position = selected[cat].index(col)
                if item_position > 0:
                    selected[cat][item_position-1], selected[cat][item_position] = selected[cat][item_position], selected[cat][item_position-1]
                    render_buttons(cat)
                    on_change(None)
            btn_priority_up.on_click(on_click_p_up)
            button_and_updown.append(btn_priority_up)

            btn = widgets.Button(description=col, layout=Layout(width='auto'))
            def on_click(b, col=col, cat=category):
                selected[cat].remove(col)
                render_buttons(cat)
                on_change(None)
            btn.on_click(on_click)
            button_and_updown.append(btn)
           
           
            buttons.append(HBox(button_and_updown))
        box.children = buttons
       
       
    for key in selected:
        render_buttons(key)

    # Columns
    columns_label = Label("Columns:")
    columns_widget = widgets.Dropdown(
        options=[None] + categorical_columns,
        value=_pivot_state['columns'] if _pivot_state['columns'] in categorical_columns else None,
        layout=Layout(width='100%')
    )

    aggfunc_label = Label("Agg function:")
    aggfunc_widget = widgets.Dropdown(
        options=['sum', 'mean', 'count', 'max', 'min'],
        value=_pivot_state['aggfunc'],
        layout=Layout(width='100%')
    )

    scale_label = Label("Scale:")
    scale_widget = widgets.Dropdown(
        options=[1, 1_000, 1_000_000, 1_000_000_000],
        value=_pivot_state['scale_factor'],
        layout=Layout(width='100%')
    )

    output = Output()

    labeled_widget_layout = Layout(
                                    grid_template_columns="20% 75%",
                                    grid_gap="1px 2%",
                                    margin='1px 0px 1px 0px'
                                )
   
    make_labeled_item = lambda item, label : GridBox(children=[Label(label), item], layout=labeled_widget_layout)
   
    grid_layout = Layout(
            grid_template_columns="45% 45%",
            grid_gap="1px 2%",
            margin='1px 0px 1px 0px'
        )
   
    control_grid = GridBox(
        children=[
            make_labeled_item(field_selector_box, "Fields"),
 
            VBox([make_labeled_item(role_selector, "Add field to") ]
                 + [ make_labeled_item(bx, ">>" + nm) for nm, bx in boxes.items() ]
                 + [make_labeled_item(columns_widget, "Columns"),
                    make_labeled_item(aggfunc_widget, "Agg function"),
                    make_labeled_item(scale_widget, "Scale"),
                   ]),
        ],
        layout=grid_layout
    )

    display(VBox([control_grid]))    
    def setup_filters(selected):
        output.clear_output()
        _pivot_state['index'] = selected[TG_INDEX].copy()
        _pivot_state['columns'] = columns_widget.value
        _pivot_state['values'] = selected[TG_VALUES].copy() #list(values_widget.value)
        _pivot_state['aggfunc'] = aggfunc_widget.value
        _pivot_state['scale_factor'] = scale_widget.value
        #if not selected[TG_INDEX] or not selected[TG_VALUES]:
        #    with output:
        #        print("Please select at least one row index and one value.")
        #    return

        with output:
            clear_output()
            row_filters = {}
            filter_widgets = []
            pivot_output = Output()
           
            full_filter_set = set(selected[TG_INDEX] + selected[TG_FILTER] + ([columns_widget.value] if columns_widget.value else []))
            for i in full_filter_set:
                options = sorted(df[i].dropna().unique().tolist())
                selected_o = [v for v in _pivot_state['filters'].get(i, options) if v in options] or options
                label = Label(f"{i}")
                widget = widgets.SelectMultiple(options=options, value=selected_o, layout=Layout(width='100%'))
                row_filters[i] = widget
                filter_widgets.append(GridBox(children=[label, widget], layout=labeled_widget_layout))

            def render_pivot():
                filtered_df = df.copy()
                for key, widget in row_filters.items():
                    vals = list(widget.value)
                    filtered_df = filtered_df[filtered_df[key].isin(vals)]
                    _pivot_state['filters'][key] = vals
               
                if selected[TG_INDEX] and selected[TG_VALUES]:
                    pivot = pd.pivot_table(
                        filtered_df,
                        index=selected[TG_INDEX],
                        columns=columns_widget.value,
                        values=selected[TG_VALUES],
                        aggfunc=aggfunc_widget.value,
                        fill_value=None
                    )

                    pivot_scaled = pivot / scale_widget.value
                    _pivot_state['last_pivot'] = pivot_scaled
                    styled = pivot_scaled.style.format("{:.1f}") if not pivot_scaled.empty else pivot_scaled
                else:
                    styled = pd.DataFrame()

                with pivot_output:
                    clear_output(wait=True)
                    display(styled)

            update_button = widgets.Button(description="Refresh")
            update_button.on_click(lambda b: render_pivot())

            filter_grid = GridBox(
                children=filter_widgets,
                layout=Layout(
                                grid_template_columns="30% 30% 30%",
                                grid_gap="1px 2%",
                                margin='1px 0px 1px 0px'
                            )
            )

            display(VBox(([Label("Filters:")] if filter_widgets else []) + [filter_grid, update_button, pivot_output]))

            if all(col in df.columns for col in selected[TG_INDEX]) and \
               (columns_widget.value is None or columns_widget.value in df.columns) and \
               all(val in df.columns for val in selected[TG_VALUES]):
                render_pivot()


    setup_filters(selected)

    def on_change(_):
        setup_filters(selected)
       
    # Main callback
    def on_select_change(change):
        role = role_selector.value.lower()
        new_items = [i for i in change['new'] if i not in selected[role]]

        for item in new_items:
            if role == TG_INDEX and item not in categorical_columns:
                continue
            if role == TG_VALUES and item not in numeric_columns:
                continue
            if item not in selected[role]:
                selected[role].append(item)
        field_selector.value = ()
        render_buttons(role)
        on_change(change)

    # Connect callback
    field_selector.observe(on_select_change, names='value')

    columns_widget.observe(on_change, names="value")
    aggfunc_widget.observe(on_change, names="value")
    scale_widget.observe(on_change, names="value")
    display(output)