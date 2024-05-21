import librosa
import numpy as np
import speech_recognition as sr
import pyaudio
import wave
import threading
import sys
from testAPI import chat_completion_request, print_conversation

class Recorder:
    def __init__(self, file_name, duration_seconds=5, sample_rate=16000, channels=1, chunk=1024, input_device_index=None):
        self.file_name = file_name
        self.duration_seconds = duration_seconds
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk = chunk
        self.input_device_index = input_device_index
        self.frames = []
        self.is_recording = False

    def start_recording(self):
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=pyaudio.paInt16,
                                      channels=self.channels,
                                      rate=self.sample_rate,
                                      input=True,
                                      input_device_index=self.input_device_index,
                                      frames_per_buffer=self.chunk)
        self.is_recording = True
        self.frames = []

        print("Recording... Press 'Enter' to stop.")

        while self.is_recording:
            data = self.stream.read(self.chunk)
            self.frames.append(data)

    def stop_recording(self):
        self.is_recording = False
        print("Finished recording")

        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

        wave_file = wave.open(self.file_name, 'wb')
        wave_file.setnchannels(self.channels)
        wave_file.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
        wave_file.setframerate(self.sample_rate)
        wave_file.writeframes(b''.join(self.frames))
        wave_file.close()

    def run(self):
        thread = threading.Thread(target=self.start_recording)
        thread.start()
        input()  # 사용자가 Enter를 누를 때까지 대기
        self.stop_recording()

class SpeechRecognizer:
    def __init__(self, file_path):
        self.file_path = file_path
        self.recognizer = sr.Recognizer()

    def recognize_speech(self):
        with sr.AudioFile(self.file_path) as source:
            audio = self.recognizer.record(source)
            try:
                # Google의 음성 인식 사용
                text = self.recognizer.recognize_google(audio, language='ko-KR')
                return text
            except sr.UnknownValueError:
                # 음성 인식 실패
                return "음성 인식에 실패했습니다."
            except sr.RequestError as e:
                # API 요청 실패
                return f"Google 음성 인식 서비스 요청에 실패했습니다; {e}"

    def print_text(self):
        # 텍스트 출력
        print(self.recognize_speech())

    def save_text_to_file(self, output_file):
        text = self.recognize_speech()
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(text)

    def calculate_metrics(self, text):
        # 단어당 분당 단어 수 및 분당 침묵 시간 계산
        num_words = len(text)
        audio_duration = librosa.get_duration(path=self.file_path)
        silence_detector = SilenceDetector(self.file_path)
        spm = silence_detector.calculate_total_silence_duration() / (audio_duration / 60)
        lpm = num_words / (audio_duration / 60)
        return lpm, spm

    def get_audio_duration(self):
        audio_duration = librosa.get_duration(path=self.file_path)

        return audio_duration

    def get_gpt_result(self, Q, A):
        messages = []
        messages.append({"role": "system",
                         "content": "당신은 면접 지원자의 답변을 피드백해주는 언어 교정과 문맥 피드백 도우미입니다. 사용자의 요청에서 질문(Q)과 답변(A) 중 하나라도 없다면 질문과 답변을 모두 입력해달라고 반드시 추가 요청합니다. 조건에 따라 사용자에게 피드백합니다."}),
        messages.append({"role": "system",
                         "content": "입력된 답변(A)에서 빈도수가 가장 높은 상위 5개의 단어와 각각의 횟수를 출력합니다.\n문맥상 불필요한 단어를 텍스트 길이에 비례해 0 ~ 10개 내의 범위 안에서 출력합니다.\n문맥에 맞지 않는 표현을 대체할 수 있는 표현을 추천합니다.\n주어진 질문에 대한 답변이 문맥상 올바른지, 그리고 교정해야할 언어 습관이 무엇인지 피드백해줍니다. 예시를 들어 피드백을 더 자세히 설명해 줄 수도 있습니다"}),
        messages.append({"role": "user",
                         "content": f"Q. {Q}\nA. {A}"}),

        print(messages)

        chat_response = chat_completion_request(messages)

        return chat_response
class SilenceDetector:
    def __init__(self, filename, sr=None):
        self.filename = filename
        self.sr = sr
        self.audio, self.sr = self.load_audio(filename)
        self.frame_length = 2048
        self.hop_length = 512
        self.energy = self.calculate_energy()
        self.threshold = 0.01  # 침묵 기준 조정 가능

    def load_audio(self, filename):
        audio, sr = librosa.load(filename, sr=self.sr)
        return audio, sr

    def calculate_energy(self):
        energy = librosa.feature.rms(y=self.audio, frame_length=self.frame_length, hop_length=self.hop_length)[0]
        return energy

    def find_silence(self):
        silence_frames = np.where(self.energy < self.threshold)[0]
        silences = []
        current_silence = [silence_frames[0]]

        for frame in silence_frames[1:]:
            if frame == current_silence[-1] + 1:
                current_silence.append(frame)
            else:
                if len(current_silence) * self.hop_length / self.sr > 0.5:  # 침묵 길이가 0.5초 이상인 경우에만 추가
                    silences.append(current_silence)
                current_silence = [frame]
        if len(current_silence) * self.hop_length / self.sr > 0.5:  # 마지막 침묵 구간이 0.5초 이상인 경우에 추가
            silences.append(current_silence)

        # 시간 단위로 변환 (초)
        silence_durations = [(len(s) * self.hop_length / self.sr, s[0] * self.hop_length / self.sr, s[-1] * self.hop_length / self.sr) for s in silences]
        return silence_durations

    def calculate_total_silence_duration(self):
        silence_durations = self.find_silence()
        total_silence_duration = sum(duration for duration, _, _ in silence_durations)
        return total_silence_duration