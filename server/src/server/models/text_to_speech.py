"""Microsoft T5 Text to Speech with Asynchronous Processing with Threads"""
import threading
import time
from queue import Queue

import torch
from datasets import load_dataset
from transformers import SpeechT5ForTextToSpeech, SpeechT5HifiGan, SpeechT5Processor


class TextToSpeechModel:
    """Initalize this class with a callback_function to handle completed requests
    asynchronously. Alternatively use the synthesise_blocking function. 
    """

    def __init__(self, callback_function):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        print(f"Device used for TextToSpeech: {self.device}")
        self.processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts",
                                                           normalize=True)

        self.model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
        self.vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")

        self.model.to(self.device)
        self.vocoder.to(self.device)

        # List of tuple of (text, callback_function)
        self.task_queue = Queue()
        self.callback_function = callback_function

        # Run in daemon so it self exits
        self.__kill_thread = False
        self.thread = threading.Thread(target=self.worker, daemon=True)
        self.thread.start()

    def __del__(self):
        self.__kill_thread = True
        self.thread.join()

    def load_speaker_embeddings(self):
        """Loads the speaker embedding, you can modify this function to load custom embeddings"""
        # self.speaker_embeddings = torch.load('models/emma_embeddings.pt')
        # self.speaker_embeddings = self.speaker_embeddings.squeeze(1)
        embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
        self.speaker_embeddings = torch.tensor(embeddings_dataset[7306]["xvector"]).unsqueeze(0)


    def synthesise(self, text, client_socket) -> None:
        """Nonblocking function to add text to worker queue, handle output via callback_function"""
        # Call load_speaker_embeddings before generating
        if self.speaker_embeddings is None:
            raise Exception("TextToSpeech: Load speaker embeddings before synthesizing")
        self.task_queue.put((client_socket, text))

    def synthesise_blocking(self, text):
        """Synthesize speech and return it, this is a blocking function"""
        inputs = self.processor(text=text, return_tensors="pt")
        start_time = time.time()
        speech = self.model.generate_speech(
                    inputs["input_ids"].to(self.device),
                    self.speaker_embeddings.to(self.device),
                    vocoder=self.vocoder,
                )
        end_time = time.time()
        print(f"synthesize : {text}. Time: {end_time - start_time}")
        return speech.cpu()

    # Don't call this code directly!
    def worker(self):
        """Worker thread event loop"""
        while not self.__kill_thread:
            if not self.task_queue.empty():
                client, text = self.task_queue.get()
                audio = self.synthesise_blocking(text)
                self.callback_function(audio, client)
                self.task_queue.task_done()
            time.sleep(0.05)
