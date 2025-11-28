@echo off
echo ==============================================
echo Creating virtual environment...
echo ==============================================
python -m venv venv

echo.
echo ==============================================
echo Activating virtual environment...
echo ==============================================
call venv\Scripts\activate

echo.
echo ==============================================
echo Upgrading pip...
echo ==============================================
pip install --upgrade pip

echo.
echo ==============================================
echo Installing required libraries...
echo ==============================================
pip install streamlit==1.38.0
pip install presidio-analyzer==2.2.351
pip install presidio-anonymizer==2.2.351
pip install spacy==3.7.5
pip install python-levenshtein==0.25.1
pip install pandas==2.2.2

echo.
echo ==============================================
echo Installing spaCy transformer model...
echo ==============================================
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_trf-3.7.3/en_core_web_trf-3.7.3-py3-none-any.whl

echo.
echo ==============================================
echo All installations completed successfully!
echo To activate the environment later, run:
echo     venv\Scripts\activate
echo ==============================================
pause
