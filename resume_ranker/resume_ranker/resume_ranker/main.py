import nltk
nltk.download('punkt')


from flask import Flask, render_template, request
from docx import Document
from difflib import SequenceMatcher
import chardet
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer

app = Flask(__name__)

def read_docx(file_path):
    doc = Document(file_path)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def detect_encoding(file_content):
    result = chardet.detect(file_content)
    return result['encoding'] if result['encoding'] is not None else 'utf-8'

def decode_file_content(file_content, encoding):
    try:
        return file_content.decode(encoding)
    except UnicodeDecodeError:
        return file_content.decode('utf-8', errors='ignore')  # Fallback to 'utf-8' with ignoring errors

def calculate_matching_percentage(job_description, resume):
    matcher = SequenceMatcher(None, job_description, resume)
    return round(matcher.ratio() * 100, 2)

def get_resume_summary(resume):
    parser = PlaintextParser.from_string(resume, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentences_count=3)  # Get a summary of 3 sentences
    return ' '.join(str(sentence) for sentence in summary)

def get_small_summary(summary):
    return summary[:100] + '...' if len(summary) > 100 else summary

def rank_resumes(job_description, resumes):
    ranked_resumes = []
    for resume in resumes:
        resume_text = read_docx(resume)
        matching_percentage = calculate_matching_percentage(job_description, resume_text)
        resume_summary = get_resume_summary(resume_text)
        small_summary = get_small_summary(resume_summary)
        ranked_resumes.append((resume, matching_percentage, small_summary))
    ranked_resumes.sort(key=lambda x: x[1], reverse=True)
    return ranked_resumes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rank', methods=['POST'])
def rank():
    job_description_file = request.files['job_description']
    job_description_content = job_description_file.read()
    job_description_encoding = detect_encoding(job_description_content)
    job_description = decode_file_content(job_description_content, job_description_encoding)
    
    resumes = request.files.getlist('resumes')
    ranked_resumes = rank_resumes(job_description, resumes)
    return render_template('result.html', ranked_resumes=ranked_resumes)

if __name__ == '__main__':
    app.run(debug=True)
