document.addEventListener('DOMContentLoaded', function () {

    // O'yin elementlari
    const elements = {
        gameContainer: document.getElementById('game-container'),
        startButton: document.getElementById('start-button'),
        restartButton: document.getElementById('restart-button'),
        levelDisplay: document.getElementById('level'),
        stageDisplay: document.getElementById('stage'),
        gridSizeDisplay: document.getElementById('grid-size'),
        scoreDisplay: document.getElementById('score'),
        timerDisplay: document.getElementById('timer'),
        statusMessage: document.getElementById('status-message'),
        musicToggle: document.getElementById('music-toggle'),
        musicIcon: document.getElementById('music-icon'),
        backgroundMusic: document.getElementById('background-music'),
        clickSound: document.getElementById('click-sound'),
        bestScore: document.getElementById('best-score'),
        maxLevel: document.getElementById('max-level'),
        maxGridSize: document.getElementById('max-grid-size'),
        gamesPlayed: document.getElementById('games-played')
    };

    // O'yin sozlamalari
    const gameConfig = {
        currentLevel: 1,
        currentStage: 1,
        stagesPerLevel: 5,
        maxLevel: 10, // 3x3 dan 50x50 gacha
        score: 0,
        sequence: [],
        playerSequence: [],
        isShowingSequence: false,
        canPlayerClick: false,
        timerInterval: null,
        timeLeft: 0,
        gameStartTime: null,
        musicEnabled: false,

        // Katakchalar soni darajaga qarab
        getGridSize(level) {
            // 3x3 dan boshlab, har darajada kattalashadi
            return level + 2;
        },

        // Har bir darajadagi ketma-ketlik uzunligi
        getSequenceLength(level, stage) {
            // Darajaga qarab boshlang'ich uzunlik
            const baseLength = Math.min(5, level + 2);
            // Bosqichga qarab qo'shimcha uzunlik
            return baseLength + Math.floor(stage / 2);
        },

        // Har bir darajadagi yonish vaqti (millisekundlarda)
        getFlashTime(level) {
            // Daraja oshgani sari yonish tezligi kamayadi
            return Math.max(400, 1200 - (level - 1) * 80);
        },

        // O'yinchi uchun javob berish vaqti (sekundlarda)
        getAnswerTime(level, sequenceLength) {
            // Ketma-ketlik uzunligi va darajaga qarab vaqt belgilanadi
            return Math.max(5, sequenceLength * 2 + level);
        }
    };

    // Foydalanuvchi statistikasini yuklash
    async function loadUserStats() {
        try {
            const response = await fetch('/api/user-stats');
            if (response.ok) {
                const stats = await response.json();
                elements.bestScore.textContent = stats.best_score;
                elements.maxLevel.textContent = stats.max_level;
                elements.maxGridSize.textContent = `${stats.max_grid_size}×${stats.max_grid_size}`;
                elements.gamesPlayed.textContent = stats.games_played;
            }
        } catch (error) {
            console.error('Failed to load user stats:', error);
        }
    }

    // O'yin maydoni katakchalarini yaratish
    function createGrid() {
        elements.gameContainer.innerHTML = '';
        const gridSize = gameConfig.getGridSize(gameConfig.currentLevel);
        elements.gridSizeDisplay.textContent = `${gridSize}×${gridSize}`;

        // Konteyner o'lchamini darajaga qarab moslash
        const maxCellSize = 80; // Maksimal katakcha o'lchami (pixels)
        const containerSize = Math.min(window.innerWidth * 0.8, 600); // Konteyner o'lchami
        const cellSize = Math.min(maxCellSize, Math.floor(containerSize / gridSize) - 4);

        const grid = document.createElement('div');
        grid.className = 'grid gap-1';
        grid.style.gridTemplateColumns = `repeat(${gridSize}, 1fr)`;
        grid.style.maxWidth = `${containerSize}px`;
        grid.style.margin = '0 auto';

        for (let i = 0; i < gridSize * gridSize; i++) {
            const cell = document.createElement('div');
            cell.className = 'bg-blue-100 hover:bg-blue-200 rounded-lg cursor-pointer transition-colors duration-200';
            cell.style.width = `${cellSize}px`;
            cell.style.height = `${cellSize}px`;
            cell.dataset.index = i;
            cell.addEventListener('click', handleCellClick);
            grid.appendChild(cell);
        }

        elements.gameContainer.appendChild(grid);
    }

    // Tasodifiy ketma-ketlik yaratish
    function generateSequence() {
        const gridSize = gameConfig.getGridSize(gameConfig.currentLevel);
        const totalCells = gridSize * gridSize;
        const sequenceLength = gameConfig.getSequenceLength(gameConfig.currentLevel, gameConfig.currentStage);

        gameConfig.sequence = [];

        for (let i = 0; i < sequenceLength; i++) {
            const randomIndex = Math.floor(Math.random() * totalCells);
            gameConfig.sequence.push(randomIndex);
        }
    }

    // Ketma-ketlikni ko'rsatish
    function showSequence() {
        gameConfig.isShowingSequence = true;
        gameConfig.canPlayerClick = false;
        elements.statusMessage.textContent = "Diqqat bilan kuzating...";
        elements.statusMessage.className = "text-lg font-medium text-center text-yellow-700 mb-6 p-3 bg-yellow-50 rounded-lg";

        let currentIndex = 0;
        const flashTime = gameConfig.getFlashTime(gameConfig.currentLevel);

        const sequenceInterval = setInterval(() => {
            if (currentIndex < gameConfig.sequence.length) {
                // Barcha katakchalarni o'chirib qo'yish
                const cells = elements.gameContainer.querySelectorAll('div[data-index]');
                cells.forEach(cell => {
                    cell.classList.remove('bg-blue-500');
                    cell.classList.add('bg-blue-100');
                });

                // Hozirgi ketma-ketlikni yoqish
                const index = gameConfig.sequence[currentIndex];
                const cell = elements.gameContainer.querySelector(`div[data-index="${index}"]`);
                cell.classList.remove('bg-blue-100');
                cell.classList.add('bg-blue-500');

                // Tovush chiqarish
                if (gameConfig.musicEnabled) {
                    elements.clickSound.currentTime = 0;
                    elements.clickSound.play();
                }

                // Yongan katakchani o'chirish
                setTimeout(() => {
                    cell.classList.remove('bg-blue-500');
                    cell.classList.add('bg-blue-100');
                }, flashTime * 0.7);

                currentIndex++;
            } else {
                clearInterval(sequenceInterval);
                gameConfig.isShowingSequence = false;
                gameConfig.canPlayerClick = true;
                gameConfig.playerSequence = [];

                elements.statusMessage.textContent = "Endi ketma-ketlikni takrorlang!";
                elements.statusMessage.className = "text-lg font-medium text-center text-green-700 mb-6 p-3 bg-green-50 rounded-lg";
                startTimer();
            }
        }, flashTime);
    }

    // Timer boshlash
    function startTimer() {
        if (gameConfig.timerInterval) {
            clearInterval(gameConfig.timerInterval);
        }

        const sequenceLength = gameConfig.sequence.length;
        gameConfig.timeLeft = gameConfig.getAnswerTime(gameConfig.currentLevel, sequenceLength);
        elements.timerDisplay.textContent = gameConfig.timeLeft;

        gameConfig.timerInterval = setInterval(() => {
            gameConfig.timeLeft--;
            elements.timerDisplay.textContent = gameConfig.timeLeft;

            if (gameConfig.timeLeft <= 0) {
                clearInterval(gameConfig.timerInterval);
                gameOver("Vaqt tugadi!");
            }
        }, 1000);
    }

    // Katak bosilgandagi harakat
    function handleCellClick(event) {
        if (!gameConfig.canPlayerClick || gameConfig.isShowingSequence) return;

        const clickedIndex = parseInt(event.target.dataset.index);
        gameConfig.playerSequence.push(clickedIndex);

        // Visual feedback
        event.target.classList.remove('bg-blue-100');
        event.target.classList.add('bg-blue-500');

        // Tovush chiqarish
        if (gameConfig.musicEnabled) {
            elements.clickSound.currentTime = 0;
            elements.clickSound.play();
        }

        setTimeout(() => {
            event.target.classList.remove('bg-blue-500');
            event.target.classList.add('bg-blue-100');
        }, 300);

        // Tekshirish
        const currentIndex = gameConfig.playerSequence.length - 1;

        // Xato kiritilgan
        if (gameConfig.playerSequence[currentIndex] !== gameConfig.sequence[currentIndex]) {
            gameOver("Xato! Qayta urining.");
            return;
        }

        // To'g'ri kiritilgan, ketma-ketlik to'liq
        if (gameConfig.playerSequence.length === gameConfig.sequence.length) {
            clearInterval(gameConfig.timerInterval);

            // O'yin davom etish
            gameConfig.score += gameConfig.currentLevel * gameConfig.currentStage * 10;
            elements.scoreDisplay.textContent = gameConfig.score;

            gameConfig.currentStage++;

            // Daraja tugagan bo'lsa, yangi darajaga o'tish
            if (gameConfig.currentStage > gameConfig.stagesPerLevel) {
                gameConfig.currentStage = 1;
                gameConfig.currentLevel++;

                // O'yin tugagan
                if (gameConfig.currentLevel > gameConfig.maxLevel) {
                    gameWin();
                    return;
                }

                createGrid();
            }

            updateDisplay();
            elements.statusMessage.textContent = "Juda yaxshi! Keyingi bosqichga tayyorlaning...";
            elements.statusMessage.className = "text-lg font-medium text-center text-green-700 mb-6 p-3 bg-green-50 rounded-lg";

            setTimeout(() => {
                startGame();
            }, 1500);
        }
    }

    // O'yin tugadi
    function gameOver(message) {
        gameConfig.canPlayerClick = false;
        clearInterval(gameConfig.timerInterval);

        const gameDuration = Math.floor((Date.now() - gameConfig.gameStartTime) / 1000);

        elements.statusMessage.textContent = message;
        elements.statusMessage.className = "text-lg font-medium text-center text-red-700 mb-6 p-3 bg-red-50 rounded-lg";

        elements.startButton.classList.add('hidden');
        elements.restartButton.classList.remove('hidden');

        // Natijani saqlash
        saveGameResult(false, gameDuration);
    }

    // O'yin g'alaba
    function gameWin() {
        clearInterval(gameConfig.timerInterval);

        const gameDuration = Math.floor((Date.now() - gameConfig.gameStartTime) / 1000);

        elements.statusMessage.textContent = "Tabriklaymiz! Barcha darajalarni yakunladingiz!";
        elements.statusMessage.className = "text-lg font-medium text-center text-green-700 mb-6 p-3 bg-green-50 rounded-lg";

        elements.startButton.classList.add('hidden');
        elements.restartButton.classList.remove('hidden');

        // Natijani saqlash
        saveGameResult(true, gameDuration);
    }

    // Natijani serverga saqlash
    async function saveGameResult(completed, duration) {
        try {
            const gridSize = gameConfig.getGridSize(gameConfig.currentLevel);

            const result = {
                score: gameConfig.score,
                level: gameConfig.currentLevel,
                stage: gameConfig.currentStage,
                grid_size: gridSize,
                duration: duration,
                completed: completed
            };

            const response = await fetch('/api/save-result', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(result)
            });

            if (response.ok) {
                // Statistikani qayta yuklash
                loadUserStats();
            } else {
                console.error('Failed to save game result');
            }
        } catch (error) {
            console.error('Error saving game result:', error);
        }
    }

    // Ekrandagi ma'lumotlarni yangilash
    function updateDisplay() {
        elements.levelDisplay.textContent = gameConfig.currentLevel;
        elements.stageDisplay.textContent = gameConfig.currentStage;
        elements.scoreDisplay.textContent = gameConfig.score;
        elements.gridSizeDisplay.textContent = `${gameConfig.getGridSize(gameConfig.currentLevel)}×${gameConfig.getGridSize(gameConfig.currentLevel)}`;
    }

    // O'yinni boshlash
    function startGame() {
        gameConfig.canPlayerClick = false;
        gameConfig.gameStartTime = Date.now();

        elements.statusMessage.textContent = "Tayyor bo'ling...";
        elements.statusMessage.className = "text-lg font-medium text-center text-blue-700 mb-6 p-3 bg-blue-50 rounded-lg";

        elements.startButton.classList.add('hidden');
        elements.restartButton.classList.add('hidden');

        generateSequence();

        setTimeout(() => {
            showSequence();
        }, 1000);
    }

    // O'yinni qayta boshlash
    function restartGame() {
        gameConfig.currentLevel = 1;
        gameConfig.currentStage = 1;
        gameConfig.score = 0;
        gameConfig.sequence = [];
        gameConfig.playerSequence = [];

        elements.startButton.classList.remove('hidden');
        elements.restartButton.classList.add('hidden');

        createGrid();
        updateDisplay();

        elements.statusMessage.textContent = "Tayyor bo'lganingizda \"Boshlash\" tugmasini bosing";
        elements.statusMessage.className = "text-lg font-medium text-center text-gray-700 mb-6 p-3 bg-gray-50 rounded-lg";
    }

    // Musiqani yoqish/o'chirish
    function toggleMusic() {
        gameConfig.musicEnabled = !gameConfig.musicEnabled;

        if (gameConfig.musicEnabled) {
            elements.musicIcon.className = 'fas fa-volume-up';
           elements.backgroundMusic.play();
       } else {
           elements.musicIcon.className = 'fas fa-volume-mute';
           elements.backgroundMusic.pause();
       }
   }

   // Event listeners
   elements.startButton.addEventListener('click', startGame);
   elements.restartButton.addEventListener('click', restartGame);
   elements.musicToggle.addEventListener('click', toggleMusic);

   // Dastlabki sozlash
   createGrid();
   updateDisplay();
   loadUserStats();

   // Quyidagi qator bilan brauzerning o'z xususiyatlari bilan o'yinni ochib olishi oldini olamiz
   document.addEventListener('keydown', function (e) {
       if ((e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'i')) ||
           (e.ctrlKey && e.shiftKey && (e.key === 'J' || e.key === 'j')) ||
           (e.key === 'F12')) {
           e.preventDefault();
       }
   });
});