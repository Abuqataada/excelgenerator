import re
import pandas as pd
from flask import Flask, request, render_template, send_file
import io

app = Flask(__name__)

def parse_mcqs(file_content):
    lines = file_content.strip().split("\n")  # Split into lines
    mcqs = []
    question = None
    options = {}
    correct_option = "N/A"

    # Regular expression to detect option prefixes (A., A), (A), a., a), (a))
    option_pattern = re.compile(r"^[\(\[]?[A-Da-d][)\].]?\s*")

    for line in lines:
        line = line.strip()
        
        if not line:  # If empty line, assume it's a separator between MCQs
            if question:  # If we have a question, save it before resetting
                mcqs.append({
                    "Question": question,
                    "Option 1 (correct)": correct_option,
                    "Option 2": options.get("A", ""),
                    "Option 3": options.get("B", ""),
                    "Option 4": options.get("C", ""),
                    "Option 5": options.get("D", "") if "D" in options else ""  # Ensure at least 4 options
                })
                question = None
                options = {}
                correct_option = "N/A"
            continue  # Skip empty line

        if re.match(r"^\d+\.", line) or not re.match(option_pattern, line):  
            # This is a new question (starts with number OR doesn't match an option format)
            question = re.sub(r"^\(?\d+\)?[.)]?\s*", "", line).strip()
            options = {}
            correct_option = "N/A"

        else:
            # This is an option
            option_text = option_pattern.sub("", line).strip()  # Remove option prefix
            if option_text.endswith("*"):  # Identify correct answer
                correct_option = option_text[:-1].strip()  # Remove '*' from correct option

            options[chr(65 + len(options))] = re.sub(r"\*$", "", option_text)  # Store cleaned option

    # Save the last question if any
    if question:
        mcqs.append({
            "Question": question,
            "Option 1 (correct)": correct_option,
            "Option 2": options.get("A", ""),
            "Option 3": options.get("B", ""),
            "Option 4": options.get("C", ""),
            "Option 5": options.get("D", "") if "D" in options else ""  # Ensure at least 4 options
        })

    return mcqs


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        uploaded_file = request.files["file"]
        filename = request.form["filename"].strip() + ".xlsx"

        if uploaded_file:
            file_content = uploaded_file.read().decode("utf-8")  # Read and decode file content
            mcqs = parse_mcqs(file_content)  # Pass file content to function

            if not mcqs:
                return "Error: No valid MCQs found!"

            # Convert to DataFrame
            df = pd.DataFrame(mcqs)

            # Create an in-memory BytesIO object
            output = io.BytesIO()

            # Write to Excel with `xlsxwriter`
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False, sheet_name="MCQs")

                # **Set column widths**
                workbook = writer.book
                worksheet = writer.sheets["MCQs"]
                column_widths = [19.29, 19.29, 19.29, 19.29, 19.29, 19.29]  # Adjust column widths as needed

                for i, width in enumerate(column_widths):
                    worksheet.set_column(i, i, width)  # Set column width
                
            output.seek(0)

            return send_file(output, as_attachment=True, download_name=filename, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)