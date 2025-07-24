import speech_recognition as sr

def transcribe_from_microphone(auto_language="vi-VN", timeout=5):
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("Mời bạn nói... ")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)

            audio = recognizer.listen(source, timeout=timeout)

            print("Đang xử lý...")
            text = recognizer.recognize_google(audio, language=auto_language)
            return text

    except sr.WaitTimeoutError:
        return "Không phát hiện giọng nói trong thời gian chờ."
    except sr.UnknownValueError:
        return "Không hiểu nội dung bạn nói."
    except sr.RequestError as e:
        return f"Lỗi kết nối tới dịch vụ nhận diện: {e}"
    except Exception as e:
        return f"Lỗi khác: {e}"

# if __name__ == "__main__":
#     result = transcribe_from_microphone()
#     print("📝 Kết quả:", result)