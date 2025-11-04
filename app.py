from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from newspaper import Article
from textblob import TextBlob
import logging
import nltk
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)
logging.basicConfig(level=logging.DEBUG)

# --- Ensure NLTK resources are present at startup ---------------------------------
# Some environments don't have the NLTK corpora/tokenizers downloaded. The
# `newspaper` and `textblob` processing can raise LookupError asking users to
# run the NLTK downloader. Download missing resources automatically at startup
# to avoid that interactive prompt and return clear startup logs.
def ensure_nltk_resources(app_obj):
    resources = {
        'punkt': 'tokenizers/punkt',
        'punkt_tab': 'tokenizers/punkt_tab',
        'averaged_perceptron_tagger': 'taggers/averaged_perceptron_tagger',
        'maxent_ne_chunker': 'chunkers/maxent_ne_chunker',
        'words': 'corpora/words'
    }
    for name, path in resources.items():
        try:
            nltk.data.find(path)
            app_obj.logger.debug(f"NLTK resource found: {path}")
        except LookupError:
            try:
                app_obj.logger.info(f"NLTK resource not found: {path}. Downloading '{name}'...")
                nltk.download(name)
                app_obj.logger.info(f"Downloaded NLTK resource: {name}")
            except Exception as e:
                app_obj.logger.warning(f"Failed to download NLTK resource '{name}': {e}")

# Run the check now so missing data is prepared before handling requests.
ensure_nltk_resources(app)
# -------------------------------------------------------------------------------

@app.route('/', methods=['GET'])
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        app.logger.debug(f"Received request: {data}")
        url = data.get('url')
        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        article = Article(url)
        article.download()
        article.parse()
        article.nlp()

        if not article.text:
            return jsonify({'error': 'Unable to fetch article content'}), 400

        analysis = TextBlob(article.text)
        polarity = round(analysis.polarity, 2)
        sentiment = 'Positive' if polarity > 0 else 'Negative' if polarity < 0 else 'Neutral'
        subjectivity = analysis.subjectivity
        bias = 'Low' if subjectivity < 0.3 else 'Moderate' if subjectivity < 0.7 else 'High'
        credibility = 'True' if subjectivity < 0.5 else 'False'

        word_count = len(article.text.split())
        reading_time = f"{round(word_count / 200)} min read"

        response = {
            'title': article.title or 'N/A',
            'author': ', '.join(article.authors) if article.authors else 'N/A',
            'summary': article.summary or 'N/A',
            'sentiment': sentiment,
            'polarity': polarity,
            'bias': bias,
            'credibility': credibility,
            'word_count': word_count,
            'reading_time': reading_time
        }
        return jsonify(response), 200

    except Exception as e:
        app.logger.error(f"Error analyzing article: {str(e)}")
        return jsonify({'error': f'Failed to analyze article: {str(e)}'}), 500


@app.route('/analyze_local', methods=['GET'])
def analyze_local():
    """Analyze a local sample article file (sample_article.txt) and return the
    same analysis JSON as `/analyze`. This is a small helper to verify the
    analysis pipeline without relying on remote HTTP fetching."""
    try:
        sample_path = os.path.join(os.path.dirname(__file__), 'sample_article.txt')
        if not os.path.exists(sample_path):
            return jsonify({'error': 'sample_article.txt not found'}), 400

        with open(sample_path, 'r', encoding='utf-8') as f:
            text = f.read()

        if not text.strip():
            return jsonify({'error': 'sample article is empty'}), 400

        analysis = TextBlob(text)
        polarity = round(analysis.polarity, 2)
        sentiment = 'Positive' if polarity > 0 else 'Negative' if polarity < 0 else 'Neutral'
        subjectivity = analysis.subjectivity
        bias = 'Low' if subjectivity < 0.3 else 'Moderate' if subjectivity < 0.7 else 'High'
        credibility = 'True' if subjectivity < 0.5 else 'False'

        word_count = len(text.split())
        reading_time = f"{round(word_count / 200)} min read"

        response = {
            'title': 'Sample Article',
            'author': 'Local Test',
            'summary': text[:300] + ('...' if len(text) > 300 else ''),
            'sentiment': sentiment,
            'polarity': polarity,
            'bias': bias,
            'credibility': credibility,
            'word_count': word_count,
            'reading_time': reading_time
        }
        return jsonify(response), 200
    except Exception as e:
        app.logger.error(f"Error analyzing local article: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)