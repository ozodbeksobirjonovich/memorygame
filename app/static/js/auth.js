document.addEventListener('DOMContentLoaded', function() {
    // Login shakli
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const errorMessage = document.getElementById('error-message');
            
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);
            
            try {
                const response = await fetch('/token', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Token va foydalanuvchi ma'lumotlarini saqlash
                    localStorage.setItem('token', data.access_token);
                    localStorage.setItem('user_id', data.user_id);
                    
                    // O'yin sahifasiga o'tish
                    window.location.href = '/game';
                } else {
                    errorMessage.textContent = data.detail || 'Login xatosi';
                    errorMessage.classList.remove('hidden');
                }
            } catch (error) {
                errorMessage.textContent = 'Serverga ulanishda xatolik';
                errorMessage.classList.remove('hidden');
                console.error('Login error:', error);
            }
        });
    }
    
    // Ro'yxatdan o'tish shakli
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(registerForm);
            const errorMessage = document.getElementById('error-message');
            
            try {
                const response = await fetch('/register', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    // Ro'yxatdan o'tish muvaffaqiyatli bo'lsa login sahifasiga o'tish
                    window.location.href = '/login?registered=true';
                } else {
                    errorMessage.textContent = data.detail || 'Ro\'yxatdan o\'tishda xatolik';
                    errorMessage.classList.remove('hidden');
                }
            } catch (error) {
                errorMessage.textContent = 'Serverga ulanishda xatolik';
                errorMessage.classList.remove('hidden');
                console.error('Registration error:', error);
            }
        });
    }
    
    // URL parametrlarini tekshirish
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('registered') && urlParams.get('registered') === 'true') {
        const errorMessage = document.getElementById('error-message');
        if (errorMessage) {
            errorMessage.textContent = 'Ro\'yxatdan muvaffaqiyatli o\'tdingiz. Endi tizimga kirishingiz mumkin.';
            errorMessage.classList.remove('hidden');
            errorMessage.classList.add('bg-green-500');
        }
    }
});