import {
  bindHoverClearsKeyboardFocus,
  isKeyboardUiMode,
  onUiInputModeChange,
  setUiInputMode,
} from './input-mode.js?v=1';

export class StorySelectorController {
  constructor() {
    this.screen = document.getElementById('story-selector-screen');
    this.listEl = document.getElementById('story-selector-list');
    this.errorEl = document.getElementById('story-selector-error');
    this.isOpen = false;
    this.selectedIndex = 0;
    this.onSelect = null;
    this.stories = [];
    this._onKeyDown = (event) => this.#handleKeyDown(event);

    if (this.screen) {
      bindHoverClearsKeyboardFocus(this.screen, () => this.highlightSelection());
    }
    onUiInputModeChange(() => {
      if (this.isOpen) this.highlightSelection();
    });
  }

  #handleKeyDown(event) {
    if (!this.isOpen) return;
    const buttons = this.getButtons();
    if (buttons.length === 0) return;

    if (event.key === 'ArrowDown' || event.key === 'ArrowRight') {
      event.preventDefault();
      setUiInputMode('keyboard');
      this.selectedIndex = (this.selectedIndex + 1) % buttons.length;
      this.highlightSelection();
    } else if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') {
      event.preventDefault();
      setUiInputMode('keyboard');
      this.selectedIndex = (this.selectedIndex - 1 + buttons.length) % buttons.length;
      this.highlightSelection();
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      buttons[this.selectedIndex]?.click();
    }
  }

  getButtons() {
    if (!this.listEl) return [];
    return [...this.listEl.querySelectorAll('button.story-card-btn:not(:disabled)')];
  }

  highlightSelection() {
    const buttons = this.getButtons();
    buttons.forEach((btn) => btn.classList.remove('menu-selected'));
    if (!isKeyboardUiMode() || buttons.length === 0) return;
    this.selectedIndex = Math.max(0, Math.min(this.selectedIndex, buttons.length - 1));
    const current = buttons[this.selectedIndex];
    current.classList.add('menu-selected');
    current.scrollIntoView?.({ block: 'nearest' });
  }

  showError(message) {
    if (!this.errorEl) return;
    if (message) {
      this.errorEl.textContent = String(message);
      this.errorEl.classList.remove('hidden');
    } else {
      this.errorEl.textContent = '';
      this.errorEl.classList.add('hidden');
    }
  }

  show(stories = [], { onSelect = null, errorMessage = '' } = {}) {
    if (!this.screen || !this.listEl) return;
    this.stories = Array.isArray(stories) ? stories : [];
    this.onSelect = onSelect;
    this.selectedIndex = 0;
    this.listEl.replaceChildren();
    this.showError(errorMessage);

    for (const story of this.stories) {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'story-card-btn';
      btn.dataset.storyId = story.id;

      if (story.cover) {
        const img = document.createElement('img');
        img.className = 'story-card-cover';
        img.src = story.cover;
        img.alt = story.title;
        img.addEventListener('error', () => {
          img.classList.add('hidden');
        });
        btn.appendChild(img);
      }

      const meta = document.createElement('div');
      meta.className = 'story-card-meta';

      const title = document.createElement('span');
      title.className = 'story-card-title';
      title.textContent = story.title;
      meta.appendChild(title);

      if (story.description) {
        const desc = document.createElement('span');
        desc.className = 'story-card-desc';
        desc.textContent = story.description;
        meta.appendChild(desc);
      }

      btn.appendChild(meta);
      btn.addEventListener('click', () => {
        this.onSelect?.(story);
      });
      this.listEl.appendChild(btn);
    }

    this.isOpen = true;
    this.screen.classList.remove('hidden');
    window.addEventListener('keydown', this._onKeyDown);
    this.highlightSelection();
  }

  hide() {
    this.isOpen = false;
    window.removeEventListener('keydown', this._onKeyDown);
    this.screen?.classList.add('hidden');
  }
}
