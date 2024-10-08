import colorsys

import streamlit as st
import streamlit.components.v1 as components


def get_color(value, min_value, max_value):
    # Convert the value to a hue between 0 and 1
    hue = (value - min_value) / (max_value - min_value)
    # Convert HSV to RGB
    rgb = colorsys.hsv_to_rgb(hue, 1, 1)
    # Convert RGB to hex
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))

def color_changing_select_slider():
    st.title("Color-Changing Select Slider")

    options = list(range(0, 101, 10))
    value = st.select_slider("Select a value", options=options)

    color = get_color(value, min(options), max(options))

    # Custom HTML and JavaScript for the color-changing slider
    custom_slider = """
    <div id="custom-slider" style="
        width: 100%;
        height: 20px;
        background: linear-gradient(to right, #ff0000, #00ff00, #0000ff);
        position: relative;
        margin-top: 20px;
    ">
        <div id="slider-handle" style="
            width: 20px;
            height: 30px;
            background-color: {color};
            position: absolute;
            top: -5px;
            left: {value}%;
            transform: translateX(-50%);
            border-radius: 5px;
            cursor: pointer;
        "></div>
    </div>
    <p id="slider-value" style="text-align: center; margin-top: 10px;">Value: {value}</p>

    <script>
        const slider = document.getElementById('custom-slider');
        const handle = document.getElementById('slider-handle');
        const valueDisplay = document.getElementById('slider-value');

        let isDragging = false;

        handle.addEventListener('mousedown', (e) => {{
            isDragging = true;
            updateSlider(e);
        }});

        document.addEventListener('mousemove', (e) => {{
            if (isDragging) {{
                updateSlider(e);
            }}
        }});

        document.addEventListener('mouseup', () => {{
            isDragging = false;
        }});

        function updateSlider(e) {{
            const rect = slider.getBoundingClientRect();
            let x = e.clientX - rect.left;
            x = Math.max(0, Math.min(x, rect.width));

            const percentage = (x / rect.width) * 100;
            handle.style.left = `${{percentage}}%`;

            const value = Math.round(percentage / 10) * 10;
            valueDisplay.textContent = `Value: ${value}`;

            // Update Streamlit
            Streamlit.setComponentValue(value);
        }}
    </script>
    """.format(color=color, value=value)

    components.html(custom_slider, height=100)

    st.write(f"Selected value: {value}")
    st.write(f"Color: {color}")

if __name__ == "__main__":
    color_changing_select_slider()