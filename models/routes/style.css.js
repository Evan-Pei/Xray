body {
  margin: 0;
  font-family: Arial, sans-serif;
  background: #f4f6f8;
  color: #1f2933;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: #0f4c81;
  color: #fff;
}

.topbar nav {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.topbar form {
  margin: 0;
}

.topbar button,
.booking-form button,
.auth-form button {
  cursor: pointer;
}

.page {
  padding: 1rem 1.5rem 2rem;
}

.layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 1rem;
}

.panel,
.calendar-panel,
.auth-card {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(15, 76, 129, 0.08);
  padding: 1rem;
}

.booking-form,
.auth-form {
  display: grid;
  gap: 0.75rem;
}

.booking-form label,
.auth-form label {
  display: grid;
  gap: 0.35rem;
  font-size: 0.95rem;
}

.booking-form input,
.booking-form select,
.booking-form textarea,
.auth-form input {
  padding: 0.6rem 0.7rem;
  border: 1px solid #cbd2d9;
  border-radius: 6px;
  font: inherit;
}

.actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

button {
  border: none;
  border-radius: 6px;
  padding: 0.65rem 0.9rem;
  background: #0f62fe;
  color: #fff;
}

button.secondary {
  background: #7b8794;
}

button.danger {
  background: #d64545;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.message {
  min-height: 1.5rem;
  margin: 0.75rem 0;
  color: #0f4c81;
}

.history-list,
.flash-list {
  padding-left: 1.25rem;
}

.auth-card {
  max-width: 420px;
  margin: 3rem auto;
}

#calendar {
  min-height: 720px;
}

@media (max-width: 960px) {
  .layout {
    grid-template-columns: 1fr;
  }

  #calendar {
    min-height: 600px;
  }
}