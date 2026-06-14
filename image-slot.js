/*
 * image-slot.js — BRDG drag-and-drop photo slot
 * ------------------------------------------------------------------
 * A tiny custom element used by the BRDG · Photographer Spotlight
 * template. Each <image-slot> is a named photo layer:
 *
 *   <image-slot id="personal-shot" label="PERSONAL SHOT" fit="cover"></image-slot>
 *
 * Behaviour
 *   • Drop an image file on it (or click to pick one) and it fills.
 *   • It REMEMBERS what you drop — the photo is cached in localStorage
 *     keyed by the slot's id, so reloading the template keeps your set.
 *   • Slots are SHARED BY ID. Drop a portrait on any slot with
 *     id="personal-shot" and every slot with that id updates at once —
 *     which is how one upload appears in both the carousel and the story.
 *
 * Attributes
 *   id    — the layer name (personal-shot, work-01 … work-04). Required.
 *   src   — initial image path (used only when nothing has been dropped).
 *   fit   — "cover" (default) or "contain" → object-fit.
 *   label — placeholder caption shown while the slot is empty.
 */
(function () {
  'use strict';

  var STORE_PREFIX = 'brdg-slot:';

  // id -> dataURL (the live, in-memory source of truth for the page)
  var sources = {};
  // id -> Set<ImageSlot> (every instance sharing that id)
  var instances = {};

  function loadFromStorage(id) {
    try {
      return window.localStorage.getItem(STORE_PREFIX + id);
    } catch (e) {
      return null;
    }
  }

  function saveToStorage(id, dataUrl) {
    try {
      window.localStorage.setItem(STORE_PREFIX + id, dataUrl);
    } catch (e) {
      // Quota is easy to blow with 5 full-res photos as base64 —
      // fall back to in-memory only so the page still works this session.
      console.warn('[image-slot] could not persist "' + id + '" (storage full?). Keeping it in memory only.');
    }
  }

  // Push a new image to every slot that shares this id, and remember it.
  function setImage(id, dataUrl) {
    sources[id] = dataUrl;
    saveToStorage(id, dataUrl);
    var set = instances[id];
    if (set) {
      set.forEach(function (el) { el.applySource(dataUrl); });
    }
  }

  function clearImage(id) {
    delete sources[id];
    try { window.localStorage.removeItem(STORE_PREFIX + id); } catch (e) {}
    var set = instances[id];
    if (set) {
      set.forEach(function (el) { el.applySource(null); });
    }
  }

  // Clear every dropped photo across all slots (used by "Reset photos").
  function clearAll() {
    Object.keys(instances).forEach(function (id) { clearImage(id); });
  }

  function readFileAsDataUrl(file, cb) {
    if (!file || !/^image\//.test(file.type)) return;
    var reader = new FileReader();
    reader.onload = function () { cb(reader.result); };
    reader.readAsDataURL(file);
  }

  var ImageSlot = (function () {
    function ImageSlot() {
      return Reflect.construct(HTMLElement, [], ImageSlot);
    }
    ImageSlot.prototype = Object.create(HTMLElement.prototype);
    ImageSlot.prototype.constructor = ImageSlot;

    ImageSlot.observedAttributes = ['src', 'fit', 'label'];

    ImageSlot.prototype.connectedCallback = function () {
      if (this._built) { this.register(); return; }
      this._built = true;

      this.style.position = 'relative';
      this.style.display = 'block';
      this.style.overflow = 'hidden';
      this.style.width = '100%';
      this.style.height = '100%';
      this.style.background = '#1b1b1b';

      // The image layer — a background-image div. html2canvas renders
      // background-size:cover correctly, but ignores object-fit on <img>
      // (which made portraits float un-cropped in the tall story frames).
      this._img = document.createElement('div');
      this._img.style.position = 'absolute';
      this._img.style.inset = '0';
      this._img.style.backgroundRepeat = 'no-repeat';
      this._img.style.backgroundPosition = 'center';
      this._img.style.display = 'none';
      this.applyFit(this.getAttribute('fit') || 'cover');
      this.appendChild(this._img);

      // The empty-state placeholder (drag target affordance).
      this._ph = document.createElement('div');
      this._ph.className = 'image-slot__placeholder';
      this._ph.setAttribute('data-slot-ui', '');
      this._ph.style.cssText = [
        'position:absolute', 'inset:0', 'display:flex',
        'flex-direction:column', 'align-items:center', 'justify-content:center',
        'gap:10px', 'text-align:center', 'padding:24px', 'box-sizing:border-box',
        'font-family:Montserrat,system-ui,sans-serif', 'color:rgba(244,241,234,0.6)',
        'background:repeating-linear-gradient(45deg,#1d1d1d,#1d1d1d 16px,#202020 16px,#202020 32px)',
        'cursor:pointer', 'transition:background .15s ease, color .15s ease'
      ].join(';');
      this._ph.innerHTML =
        '<div style="width:34px;height:34px;border-radius:50%;border:1.5px solid currentColor;' +
        'display:flex;align-items:center;justify-content:center;font-size:18px;line-height:1">+</div>' +
        '<div style="font-size:13px;font-weight:700;letter-spacing:2px;text-transform:uppercase" data-ph-label></div>' +
        '<div style="font-size:11px;font-weight:500;letter-spacing:.5px;opacity:.8">drop photo · or click</div>';
      this.appendChild(this._ph);

      // Hidden file input for click-to-pick.
      this._file = document.createElement('input');
      this._file.type = 'file';
      this._file.accept = 'image/*';
      this._file.style.display = 'none';
      this.appendChild(this._file);

      this.updateLabel();
      this.wireEvents();
      this.register();

      // Decide what to show: a remembered drop wins over the src attribute.
      var id = this.getAttribute('id');
      var remembered = (id && (sources[id] || loadFromStorage(id))) || null;
      if (remembered) {
        sources[id] = remembered;
        this.applySource(remembered);
      } else if (this.getAttribute('src')) {
        this.applySource(this.getAttribute('src'));
      } else {
        this.applySource(null);
      }
    };

    ImageSlot.prototype.disconnectedCallback = function () {
      var id = this.getAttribute('id');
      if (id && instances[id]) instances[id].delete(this);
    };

    ImageSlot.prototype.register = function () {
      var id = this.getAttribute('id');
      if (!id) return;
      if (!instances[id]) instances[id] = new Set();
      instances[id].add(this);
    };

    ImageSlot.prototype.attributeChangedCallback = function (name, oldV, newV) {
      if (!this._built) return;
      if (name === 'fit') this.applyFit(newV || 'cover');
      if (name === 'label') this.updateLabel();
      if (name === 'src') {
        // Setting src programmatically (the Claude route) only takes effect
        // if nothing has been dropped onto this id.
        var id = this.getAttribute('id');
        if (!(id && sources[id])) this.applySource(newV);
      }
    };

    ImageSlot.prototype.applyFit = function (fit) {
      if (this._img) this._img.style.backgroundSize = (fit === 'contain') ? 'contain' : 'cover';
    };

    ImageSlot.prototype.updateLabel = function () {
      if (!this._ph) return;
      var label = this.getAttribute('label') || this.getAttribute('id') || 'PHOTO';
      var node = this._ph.querySelector('[data-ph-label]');
      if (node) node.textContent = label;
    };

    ImageSlot.prototype.applySource = function (src) {
      if (src) {
        this._img.style.backgroundImage = 'url("' + src + '")';
        this._img.style.display = 'block';
        this._ph.style.display = 'none';
        this.setAttribute('data-filled', '');
      } else {
        this._img.style.backgroundImage = '';
        this._img.style.display = 'none';
        this._ph.style.display = 'flex';
        this.removeAttribute('data-filled');
      }
    };

    ImageSlot.prototype.wireEvents = function () {
      var self = this;
      var id = this.getAttribute('id');

      this.addEventListener('dragover', function (e) {
        e.preventDefault();
        self._ph.style.color = '#D9543F';
        self.style.outline = '2px solid #D9543F';
        self.style.outlineOffset = '-2px';
      });
      function leave() {
        self._ph.style.color = 'rgba(244,241,234,0.6)';
        self.style.outline = 'none';
      }
      this.addEventListener('dragleave', leave);
      this.addEventListener('drop', function (e) {
        e.preventDefault();
        leave();
        var file = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
        readFileAsDataUrl(file, function (url) { if (id) setImage(id, url); else self.applySource(url); });
      });

      // Click empty placeholder → file picker.
      this._ph.addEventListener('click', function () { self._file.click(); });
      this._file.addEventListener('change', function () {
        var file = self._file.files && self._file.files[0];
        readFileAsDataUrl(file, function (url) {
          if (id) setImage(id, url); else self.applySource(url);
          self._file.value = '';
        });
      });
    };

    return ImageSlot;
  })();

  if (!window.customElements.get('image-slot')) {
    window.customElements.define('image-slot', ImageSlot);
  }

  // Small public API the template's Tweaks panel can call.
  window.BRDGSlots = {
    set: setImage,
    clear: clearImage,
    clearAll: clearAll,
    get: function (id) { return sources[id] || loadFromStorage(id) || null; }
  };
})();
