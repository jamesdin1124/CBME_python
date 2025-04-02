// 表單驗證和提交
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('epaForm');
    const startRecordingBtn = document.getElementById('startRecording');
    let mediaRecorder = null;
    let audioChunks = [];

    // 表單提交處理
    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        
        if (!form.checkValidity()) {
            event.stopPropagation();
            form.classList.add('was-validated');
            return;
        }

        // 收集表單數據
        const formData = {
            hierarchy: document.getElementById('hierarchy').value,
            student_id: document.getElementById('student_id').value,
            student_name: document.getElementById('student_name').value,
            location: document.getElementById('location').value,
            patient_id: document.getElementById('patient_id').value,
            clinical_scenario: document.getElementById('clinical_scenario').value,
            student_epa_level: document.getElementById('student_epa_level').value,
            patient_difficulty: document.getElementById('patient_difficulty').value,
            teacher_epa_level: document.getElementById('teacher_epa_level').value,
            feedback: document.getElementById('feedback').value
        };

        try {
            const response = await fetch('/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();
            
            if (result.status === 'success') {
                alert('表單提交成功！');
                form.reset();
                form.classList.remove('was-validated');
            } else {
                alert('提交失敗：' + result.message);
            }
        } catch (error) {
            alert('提交時發生錯誤：' + error.message);
        }
    });

    // 語音輸入功能
    startRecordingBtn.addEventListener('click', async function() {
        if (!mediaRecorder) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.addEventListener('dataavailable', event => {
                    audioChunks.push(event.data);
                });

                mediaRecorder.addEventListener('stop', async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const formData = new FormData();
                    formData.append('audio', audioBlob);

                    try {
                        const response = await fetch('/transcribe', {
                            method: 'POST',
                            body: formData
                        });

                        const result = await response.json();
                        
                        if (result.status === 'success') {
                            document.getElementById('feedback').value = result.text;
                        } else {
                            alert('語音轉換失敗：' + result.message);
                        }
                    } catch (error) {
                        alert('語音轉換時發生錯誤：' + error.message);
                    }
                });

                mediaRecorder.start();
                startRecordingBtn.textContent = '停止錄音';
                startRecordingBtn.classList.add('btn-danger');
            } catch (error) {
                alert('無法存取麥克風：' + error.message);
            }
        } else {
            mediaRecorder.stop();
            startRecordingBtn.textContent = '語音輸入';
            startRecordingBtn.classList.remove('btn-danger');
        }
    });

    // 無障礙支援：鍵盤操作
    form.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' && event.target.tagName !== 'TEXTAREA') {
            event.preventDefault();
            const nextElement = event.target.nextElementSibling;
            if (nextElement) {
                nextElement.focus();
            }
        }
    });

    // 自動儲存功能
    let autoSaveTimeout;
    const formInputs = form.querySelectorAll('input, select, textarea');
    
    formInputs.forEach(input => {
        input.addEventListener('input', function() {
            clearTimeout(autoSaveTimeout);
            autoSaveTimeout = setTimeout(() => {
                const formData = new FormData(form);
                localStorage.setItem('epaFormDraft', JSON.stringify(Object.fromEntries(formData)));
            }, 1000);
        });
    });

    // 載入草稿
    const savedDraft = localStorage.getItem('epaFormDraft');
    if (savedDraft) {
        const draftData = JSON.parse(savedDraft);
        Object.keys(draftData).forEach(key => {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) {
                input.value = draftData[key];
            }
        });
        form.classList.add('was-validated');
    }
}); 