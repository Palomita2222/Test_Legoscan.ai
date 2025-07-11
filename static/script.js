const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const results = document.getElementById('results');

navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
    .then(stream => {
        video.srcObject = stream;
    })
    .catch(err => console.error('Camera error:', err));

function capture() {
    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);

    canvas.toBlob(blob => {
        const formData = new FormData();
        formData.append('image', blob, 'capture.jpg');

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            results.innerHTML = '';
            data.codes.forEach(code => {
                const li = document.createElement('li');
                li.textContent = code;
                results.appendChild(li);
            });
        })
        .catch(err => console.error('Upload error:', err));
    }, 'image/jpeg');
}
