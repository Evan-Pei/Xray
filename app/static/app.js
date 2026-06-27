const dialog = document.getElementById('booking-dialog');
const form = document.getElementById('booking-form');
const errorBox = document.getElementById('form-error');
const deleteButton = document.getElementById('delete-booking-button');
const closeButton = document.getElementById('close-dialog-button');
const newBookingButton = document.getElementById('new-booking-button');
const title = document.getElementById('dialog-title');

const fields = {
  id: document.getElementById('booking-id'),
  applicant_name: document.getElementById('applicant_name'),
  machine_name: document.getElementById('machine_name'),
  purpose: document.getElementById('purpose'),
  start_time: document.getElementById('start_time'),
  end_time: document.getElementById('end_time'),
  status: document.getElementById('status'),
  actual_start: document.getElementById('actual_start'),
  actual_end: document.getElementById('actual_end'),
  usage_notes: document.getElementById('usage_notes'),
};

function toLocalInputValue(value) {
  if (!value) return '';
  const date = new Date(value);
  const offset = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - offset).toISOString().slice(0, 16);
}

function toPayload() {
  return {
    applicant_name: fields.applicant_name.value.trim(),
    machine_name: fields.machine_name.value.trim(),
    purpose: fields.purpose.value.trim(),
    start_time: new Date(fields.start_time.value).toISOString(),
    end_time: new Date(fields.end_time.value).toISOString(),
    status: fields.status.value,
    actual_start: fields.actual_start.value ? new Date(fields.actual_start.value).toISOString() : null,
    actual_end: fields.actual_end.value ? new Date(fields.actual_end.value).toISOString() : null,
    usage_notes: fields.usage_notes.value.trim() || null,
  };
}

function setError(message) {
  if (!message) {
    errorBox.hidden = true;
    errorBox.textContent = '';
    return;
  }
  errorBox.hidden = false;
  errorBox.textContent = message;
}

function resetForm() {
  form.reset();
  fields.id.value = '';
  fields.status.value = 'pending';
  deleteButton.hidden = true;
  setError('');
}

function openCreateDialog(startValue, endValue) {
  resetForm();
  title.textContent = 'Create Booking';
  fields.start_time.value = startValue || '';
  fields.end_time.value = endValue || '';
  dialog.showModal();
}

async function openEditDialog(bookingId) {
  resetForm();
  const response = await fetch(`/api/bookings/${bookingId}`);
  const booking = await response.json();
  title.textContent = 'Edit Booking';
  fields.id.value = booking.id;
  fields.applicant_name.value = booking.applicant_name;
  fields.machine_name.value = booking.machine_name;
  fields.purpose.value = booking.purpose;
  fields.start_time.value = toLocalInputValue(booking.start_time);
  fields.end_time.value = toLocalInputValue(booking.end_time);
  fields.status.value = booking.status;
  fields.actual_start.value = toLocalInputValue(booking.actual_start);
  fields.actual_end.value = toLocalInputValue(booking.actual_end);
  fields.usage_notes.value = booking.usage_notes || '';
  deleteButton.hidden = false;
  dialog.showModal();
}

closeButton.addEventListener('click', () => dialog.close());
newBookingButton.addEventListener('click', () => openCreateDialog());

deleteButton.addEventListener('click', async () => {
  const bookingId = fields.id.value;
  if (!bookingId) return;
  const response = await fetch(`/api/bookings/${bookingId}`, { method: 'DELETE' });
  if (!response.ok) {
    const payload = await response.json();
    setError(payload.detail || 'Unable to delete booking');
    return;
  }
  dialog.close();
  calendar.refetchEvents();
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  setError('');

  const bookingId = fields.id.value;
  const method = bookingId ? 'PUT' : 'POST';
  const url = bookingId ? `/api/bookings/${bookingId}` : '/api/bookings';
  const response = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(toPayload()),
  });

  if (!response.ok) {
    const payload = await response.json();
    const message = payload.detail || payload.message || 'Unable to save booking';
    setError(typeof message === 'string' ? message : JSON.stringify(message));
    return;
  }

  dialog.close();
  calendar.refetchEvents();
});

const calendar = new FullCalendar.Calendar(document.getElementById('calendar'), {
  initialView: 'dayGridMonth',
  selectable: true,
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: 'dayGridMonth,timeGridWeek,timeGridDay',
  },
  initialDate: new Date(window.XRAY_DEFAULT_MONTH.year, window.XRAY_DEFAULT_MONTH.month - 1, 1),
  events(fetchInfo, successCallback, failureCallback) {
    const target = calendar.getDate();
    const year = target.getFullYear();
    const month = target.getMonth() + 1;
    fetch(`/api/bookings?year=${year}&month=${month}`)
      .then((response) => {
        if (!response.ok) throw new Error('Failed to load bookings');
        return response.json();
      })
      .then(successCallback)
      .catch(failureCallback);
  },
  dateClick(info) {
    const start = `${info.dateStr}T09:00`;
    const end = `${info.dateStr}T10:00`;
    openCreateDialog(start, end);
  },
  eventClick(info) {
    openEditDialog(info.event.id);
  },
  select(info) {
    openCreateDialog(toLocalInputValue(info.start), toLocalInputValue(info.end));
  },
});

calendar.render();
