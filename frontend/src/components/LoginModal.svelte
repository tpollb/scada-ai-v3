<script lang="ts">
  import { auth } from '../stores/auth'
  import { X, Lock, LogIn } from 'lucide-svelte'

  let username = $state('')
  let password = $state('')
  let showPassword = $state(false)
  let isSubmitting = $state(false)
  let localError = $state<string | null>(null)

  async function handleSubmit() {
    if (!username || !password) {
      localError = 'Введите имя пользователя и пароль'
      return
    }

    isSubmitting = true
    localError = null

    try {
      await auth.login(username, password)
      // Успешный вход - компонент будет скрыт через App.svelte
      username = ''
      password = ''
    } catch (error) {
      localError = error instanceof Error ? error.message : 'Ошибка входа'
    } finally {
      isSubmitting = false
    }
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter') {
      handleSubmit()
    }
  }
</script>

<div class="auth-modal-overlay">
  <div class="auth-modal">
    <div class="auth-modal-header">
      <div class="auth-modal-title">
        <Lock size={24} />
        <h2>Авторизация SCADA AI</h2>
      </div>
      <p class="auth-modal-subtitle">
        Введите учетные данные для доступа к системе
      </p>
    </div>

    <form class="auth-modal-form" on:submit|preventDefault={handleSubmit}>
      <div class="auth-input-group">
        <label for="username">Имя пользователя</label>
        <input
          id="username"
          type="text"
          bind:value={username}
          on:keydown={handleKeydown}
          placeholder="admin, engineer, operator, boss"
          disabled={isSubmitting}
          autocomplete="username"
        />
      </div>

      <div class="auth-input-group">
        <label for="password">Пароль</label>
        <div class="auth-password-input">
          <input
            id="password"
            :type={showPassword ? 'text' : 'password'}
            bind:value={password}
            on:keydown={handleKeydown}
            placeholder="••••••••"
            disabled={isSubmitting}
            autocomplete="current-password"
          />
          <button
            type="button"
            class="auth-toggle-password"
            on:click={() => showPassword = !showPassword}
            disabled={isSubmitting}
          >
            {showPassword ? '🙈' : '👁️'}
          </button>
        </div>
      </div>

      {#if localError || $auth.error}
        <div class="auth-error">
          {localError || $auth.error}
        </div>
      {/if}

      <button
        type="submit"
        class="auth-submit-btn"
        disabled={isSubmitting || !username || !password}
      >
        {#if isSubmitting}
          <span class="auth-loading-spinner"></span>
          Вход...
        {:else}
          <LogIn size={18} />
          Войти
        {/if}
      </button>
    </form>

    <div class="auth-modal-footer">
      <p class="auth-hint">
        <strong>Предустановленные пользователи:</strong>
      </p>
      <div class="auth-users-grid">
        <div class="auth-user-item">
          <code>admin / admin123</code>
          <span>Администратор</span>
        </div>
        <div class="auth-user-item">
          <code>engineer / engineer123</code>
          <span>Инженер</span>
        </div>
        <div class="auth-user-item">
          <code>operator / operator123</code>
          <span>Оператор</span>
        </div>
        <div class="auth-user-item">
          <code>boss / boss123</code>
          <span>Руководитель</span>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .auth-modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9999;
    animation: fadeIn 0.2s ease-out;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .auth-modal {
    background: var(--bg-primary, #ffffff);
    border-radius: 16px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    max-width: 480px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
    animation: slideUp 0.3s ease-out;
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .auth-modal-header {
    padding: 2rem 2rem 1rem;
    text-align: center;
  }

  .auth-modal-title {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    color: var(--text-primary, #1a1a1a);
    margin-bottom: 0.5rem;
  }

  .auth-modal-title h2 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
  }

  .auth-modal-subtitle {
    margin: 0;
    color: var(--text-secondary, #666);
    font-size: 0.9rem;
  }

  .auth-modal-form {
    padding: 1rem 2rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .auth-input-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .auth-input-group label {
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--text-primary, #1a1a1a);
  }

  .auth-input-group input {
    padding: 0.75rem 1rem;
    border: 2px solid var(--border-color, #e0e0e0);
    border-radius: 8px;
    font-size: 1rem;
    background: var(--bg-secondary, #f5f5f5);
    color: var(--text-primary, #1a1a1a);
    transition: all 0.2s;
  }

  .auth-input-group input:focus {
    outline: none;
    border-color: var(--accent-color, #3b82f6);
    background: var(--bg-primary, #ffffff);
  }

  .auth-input-group input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .auth-password-input {
    position: relative;
    display: flex;
    align-items: center;
  }

  .auth-password-input input {
    flex: 1;
    padding-right: 3rem;
  }

  .auth-toggle-password {
    position: absolute;
    right: 0.75rem;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1.2rem;
    padding: 0.25rem;
    opacity: 0.6;
    transition: opacity 0.2s;
  }

  .auth-toggle-password:hover {
    opacity: 1;
  }

  .auth-toggle-password:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .auth-error {
    padding: 0.75rem 1rem;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 8px;
    color: rgba(239, 68, 68, 0.9);
    font-size: 0.9rem;
    text-align: center;
  }

  .auth-submit-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.875rem 1.5rem;
    background: var(--accent-color, #3b82f6);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  .auth-submit-btn:hover:not(:disabled) {
    background: var(--accent-hover, #2563eb);
    transform: translateY(-1px);
  }

  .auth-submit-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }

  .auth-loading-spinner {
    width: 18px;
    height: 18px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .auth-modal-footer {
    padding: 1.5rem 2rem 2rem;
    background: var(--bg-secondary, #f5f5f5);
    border-radius: 0 0 16px 16px;
  }

  .auth-hint {
    margin: 0 0 1rem;
    font-size: 0.85rem;
    color: var(--text-secondary, #666);
    text-align: center;
  }

  .auth-users-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }

  .auth-user-item {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    padding: 0.5rem 0.75rem;
    background: var(--bg-primary, #ffffff);
    border-radius: 6px;
    font-size: 0.8rem;
  }

  .auth-user-item code {
    font-family: 'Courier New', monospace;
    color: var(--accent-color, #3b82f6);
    font-weight: 600;
  }

  .auth-user-item span {
    color: var(--text-secondary, #666);
  }

  @media (max-width: 480px) {
    .auth-users-grid {
      grid-template-columns: 1fr;
    }
    
    .auth-modal {
      width: 95%;
    }
  }
</style>
