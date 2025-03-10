document.addEventListener('DOMContentLoaded', function() {
    const profileForm = document.getElementById('profile-form');
    const regionSelect = document.getElementById('region');
    const districtSelect = document.getElementById('district');
    const messageContainer = document.getElementById('message-container');
    const currentRegion = regionSelect.getAttribute('data-current');
    const currentDistrict = districtSelect.getAttribute('data-current');
    
    // Viloyat tanlaganda tumanlarni yuklash
    regionSelect.addEventListener('change', async function() {
        const region = this.value;
        if (!region) {
            districtSelect.innerHTML = '<option value="">Avval viloyatni tanlang</option>';
            districtSelect.disabled = true;
            return;
        }
        
        try {
            const response = await fetch(`/api/get-districts?region=${encodeURIComponent(region)}`);
            const data = await response.json();
            
            districtSelect.innerHTML = '';
            if (data.districts && data.districts.length > 0) {
                data.districts.forEach(district => {
                    const option = document.createElement('option');
                    option.value = district;
                    option.textContent = district;
                    
                    // Joriy tumanni tanlash
                    if (region === currentRegion && district === currentDistrict) {
                        option.selected = true;
                    }
                    
                    districtSelect.appendChild(option);
                });
                districtSelect.disabled = false;
            } else {
                districtSelect.innerHTML = '<option value="">Tumanlar topilmadi</option>';
                districtSelect.disabled = true;
            }
        } catch (error) {
            console.error('Error loading districts:', error);
        }
    });
    
    // Joriy viloyat tanlanayotganda tumanlarni yuklash
    if (currentRegion) {
        regionSelect.dispatchEvent(new Event('change'));
    }
    
    // Profil ma'lumotlarini yangilash
    if (profileForm) {
        profileForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(profileForm);
            
            try {
                const response = await fetch('/update-profile', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showMessage('success', 'Profil muvaffaqiyatli yangilandi');
                    
                    // 1 sekunddan so'ng sahifani qayta yuklash
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                    
                } else {
                    showMessage('error', data.detail || 'Profilni yangilashda xatolik');
                }
            } catch (error) {
                showMessage('error', 'Serverga ulanishda xatolik');
                console.error('Profile update error:', error);
            }
        });
    }
    
    // Xabar ko'rsatish
    function showMessage(type, text) {
        messageContainer.innerHTML = '';
        
        const messageDiv = document.createElement('div');
        messageDiv.className = type === 'success' 
            ? 'bg-green-100 border-l-4 border-green-500 text-green-700 p-4 rounded-md' 
            : 'bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded-md';
        messageDiv.textContent = text;
        
        messageContainer.appendChild(messageDiv);
        messageContainer.classList.remove('hidden');
        
        // 3 sekunddan so'ng xabarni o'chirish
        setTimeout(() => {
            messageContainer.classList.add('hidden');
        }, 3000);
    }
    
    // Rasm yuklanayotganda ko'rsatish (preview)
    const avatarInput = document.getElementById('avatar');
    const avatarPreview = document.getElementById('avatar-preview');
    
    if (avatarInput && avatarPreview) {
        avatarInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    avatarPreview.src = e.target.result;
                };
                
                reader.readAsDataURL(this.files[0]);
            }
        });
    }
});