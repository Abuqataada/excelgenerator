import io
from flask import Flask, request, render_template, send_file, flash, session, redirect, url_for
import io
import pandas as pd
import re

app = Flask(__name__)
app.secret_key = "ghnvgbhBHGFHGFH#%$^&^^%$65645#$%^$%&^%#$^&*(**^&%)"

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
            else:
                options[chr(65 + len(options))] = option_text  # Only add non-correct options. Store cleaned option

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

# Store generated file in session
stored_files = {}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        uploaded_file = request.files.get("file")
        if not uploaded_file or uploaded_file.filename == "":
            flash("Please upload a valid file!", "warning")
            return redirect(url_for("index"))

        filename = request.form["filename"].strip() + ".xlsx"
        file_content = uploaded_file.read().decode("utf-8")  # Read file content
        mcqs = parse_mcqs(file_content)

        if not mcqs:
            flash("Error: No valid MCQs found! Check your file format.", "danger")
            return redirect(url_for("index"))

        # Convert to Excel
        df = pd.DataFrame(mcqs)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name=filename[:-5]+"_Questions")

        workbook = writer.book
        worksheet = writer.sheets[filename[:-5]+"_Questions"]
        column_widths = [19.29] * 6

        for i, width in enumerate(column_widths):
            worksheet.set_column(i, i, width)

        output.seek(0)
        # Store file in dictionary with a unique key
        session['file_key'] = filename  # Store filename in session
        stored_files[filename] = output

        flash("File generated successfully! Downloading now...", "success")

        # Return HTML with JavaScript to trigger automatic download
        return render_template("index.html", auto_download=True, file_url=url_for("download"))

    return render_template("index.html")

@app.route("/download")
def download():
    """ Route to handle the actual file download """
    file_key = session.get('file_key')  # Retrieve file key from session

    if not file_key or file_key not in stored_files:
        flash("Error: File not found!", "danger")
        return redirect(url_for("index"))

    return send_file(stored_files[file_key], as_attachment=True, download_name=file_key,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)