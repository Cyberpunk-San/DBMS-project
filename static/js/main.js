document.addEventListener('DOMContentLoaded', () => {
  // -------------------------------------------------
  // 1. SOLVE CASE (with guilty suspect selection)
  // -------------------------------------------------
  document.querySelectorAll('.solve-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      const caseId = this.dataset.caseId;
      const selected = document.querySelector('input.guilty-radio:checked');

      if (!selected) {
        alert('Please select the guilty suspect first!');
        return;
      }

      const guiltyId = selected.value;

      fetch(`/case/${caseId}/solve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: `guilty_suspect=${guiltyId}`
      })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            // Play sound
            const sound = document.getElementById('caseClosedSound');
            if (sound) sound.play().catch(() => {});

            alert('CASE CLOSED! Excellent detective work!');

            // Reload to update UI
            setTimeout(() => location.reload(), 800);

            // Easter egg after 3 solved cases
            if (data.easter_egg) {
              const egg = document.createElement('div');
              egg.className = 'easter-egg';
              egg.innerHTML = 'SECRET CASE UNLOCKED!';
              document.body.appendChild(egg);

              // Auto-remove after 5 seconds
              setTimeout(() => egg.remove(), 5000);
            }
          }
        })
        .catch(err => {
          console.error('Error solving case:', err);
          alert('Something went wrong. Try again.');
        });
    });
  });

  // -------------------------------------------------
  // 2. DELETE CASE
  // -------------------------------------------------
  document.querySelectorAll('.delete-case').forEach(btn => {
    btn.addEventListener('click', function () {
      const caseId = this.dataset.id;
      if (confirm('Delete this entire case? This cannot be undone.')) {
        fetch(`/case/${caseId}/delete`, {
          method: 'POST'
        })
          .then(r => r.json())
          .then(d => {
            if (d.success) {
              alert('Case deleted.');
              window.location.href = '/dashboard';
            } else {
              alert('Failed to delete case.');
            }
          })
          .catch(() => alert('Error. Check console.'));
      }
    });
  });

  // -------------------------------------------------
  // 3. DELETE CLUE
  // -------------------------------------------------
  document.querySelectorAll('.delete-clue').forEach(btn => {
    btn.addEventListener('click', function () {
      const clueId = this.dataset.id;
      if (confirm('Delete this clue permanently?')) {
        fetch(`/clue/${clueId}/delete`, {
          method: 'POST'
        })
          .then(r => r.json())
          .then(d => {
            if (d.success) {
              this.closest('li').remove();
              alert('Clue deleted.');
            }
          })
          .catch(() => alert('Error deleting clue.'));
      }
    });
  });

  // -------------------------------------------------
  // 4. DELETE SUSPECT
  // -------------------------------------------------
  document.querySelectorAll('.delete-suspect').forEach(btn => {
    btn.addEventListener('click', function () {
      const suspectId = this.dataset.id;
      if (confirm('Delete this suspect permanently?')) {
        fetch(`/suspect/${suspectId}/delete`, {
          method: 'POST'
        })
          .then(r => r.json())
          .then(d => {
            if (d.success) {
              this.closest('li').remove();
              alert('Suspect deleted.');
            }
          })
          .catch(() => alert('Error deleting suspect.'));
      }
    });
  });

  // -------------------------------------------------
  // 5. OPTIONAL: Auto-hide flash messages
  // -------------------------------------------------
  setTimeout(() => {
    document.querySelectorAll('.alert').forEach(alert => {
      if (!alert.classList.contains('alert-danger')) {
        alert.style.transition = 'opacity 1s';
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 1000);
      }
    });
  }, 4000);
});