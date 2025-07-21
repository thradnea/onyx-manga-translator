# Onyx Manga Translator

![Onyx Manga Translator Splash](https://github.com/thradnea/onyx-manga-translator/blob/main/images/New%20Project%20(3)%20(1).png?raw=true)

Onyx is a powerful, purely locally running machine translation pipeline designed to translate manga automatically. Integrates an ML model for speech bubble detection (credits below), OCR (credits below), and typesetting to deliver a seamless translation experience right on your own machine.

This tool is designed for readers and scanlation groups who need a fast way to get initial crude, but readable translations of their favorite series.

Test runs with Jujutsu Kaisen and Blue Giant are here: (https://mega.nz/folder/ZUwBmT4C#U-x2wiALmSzCekFHcoTGeQ)

---

## Key Features

* **Automated Pipeline**: Handles the entire process from speech bubble detection to final typeset translation.
* **High-Quality OCR**: Utilizes a specialized Manga OCR model to accurately extract Japanese text from complex comic pages.
* **Machine Translation**: Leverages the Google Translate API for fast and effective text translation.
* **Automatic Typesetting**: Cleans the original text from the speech bubbles and typesets the new translated text, fitting it reasonably well to speech bubbles.
* **Fully Local**: The entire pipeline runs on your own resources with no strings attached. No images or data are uploaded to third-party servers, except for the text sent to the Google Translate API.
* **CPU Support**: Runs entirely on your CPU, with plans for CUDA support in the near future on Patreon for faster speeds.
* **Database Integration**: Integrates a SQlite database for past translations. Editing said translations can bring better results over the span of translating a particular manga, since misinterpreted words can be corrected.

---

## Getting Started

### Prerequisites

* A Google Cloud account with the Translate API enabled.
* A Google Cloud JSON credentials file.

### Installation & Usage

1. Download the full compressed archive with the PyInstaller executable inside. Extract and run. First boot will ALWAYS take longer, do not be alarmed in that case.
2. Add desired images to the input folder of manga raws in .jpg/.png formats and click "Browse" to locate the input folder.
3. Lastly, add your api.json file from Google Cloud.

4. You can also clone the repository and use it directly through an IDE by running main.py. Please note, that you still need to clone the huggingface repository by kitsumed at the bottom of the README and clone the manga-ocr repository by kha-white. The original project's structure was as follows:

(https://github.com/thradnea/onyx-manga-translator/blob/main/images/image.png?raw=true)
---

## License & Credit

This project is provided as-is and is free to use, modify, and distribute.

However, if you use this tool in any public project, **credit is greatly appreciated**.

While you are free to use this version, please note the future development model below.

---

## Future Development & Support

**This GitHub repository is an alpha snapshot and will not be regularly updated, only maintained for use.**

All future development, including smaller bug fixes, new features, and performance improvements, will be handled exclusively for supporters on Patreon. By becoming a patron, you will gain access to the latest versions of Onyx, including upcoming features:

* **CUDA Support**: GPU acceleration for significantly faster processing.
* **Expanded Language Support**: Translation support for Korean and Chinese.
* **Commercial Licenses**: Options for professional and commercial translation teams.
* **Support and suggestions**: Help with any arising issues and the ability to suggest new features in the Discord.
* **DISCLAIMER**: When you subscribe on Patreon, which will NEVER change prices (it will always be $5/mo) you are not required to re-subscribe. Subscribing once and then continuing to use the translator if you do not require frequent updates is completely fine and is encouraged. There will be no authentication except for if you've subscribed before. If you have, Onyx will never lock you out, since the purpose of this tool is to be local and non-intrusive.

<a href="https://www.patreon.com/your-patreon-link">
    <img src="https://github.com/thradnea/onyx-manga-translator/blob/main/images/patreon.png?raw=true" alt="Become a Patron" />
</a>

Your support is immensely appreciated. Thank you.
## Credits
https://huggingface.co/kitsumed/yolov8m_seg-speech-bubble
https://github.com/kha-white/manga-ocr
