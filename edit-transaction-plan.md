# Plan: Edit Transaction Feature (In-Page Modal)

## Overview

Add the ability to edit an existing transaction directly from the dashboard using an in-page modal popup. Clicking an "Edit" button on a transaction row opens a pre-filled modal form (same visual style as the "Add transaction" form). On submission, a `PUT` API call updates the record and the modal closes, refreshing the transaction list. Only the logged-in user can edit their own transactions (enforced server-side).

No new page, no redirect — everything happens on the dashboard.

---

## Sub-Task 1: Add PUT API Route in `app.py`

**Intent:** Add a `PUT /api/transactions/<id>` endpoint that validates and updates a transaction in the database. Ownership is enforced — only the logged-in user's own transaction can be updated.

**Expected Outcomes:**
- `PUT /api/transactions/<id>` returns `200` with success message when valid
- Returns `404` if transaction not found or belongs to another user
- Returns `400` for invalid input (same validations as `create_transaction`)
- Unauthenticated requests return `401`

**Todo List:**
1. Add `PUT` method handler for `/api/transactions/<int:transaction_id>` in `app.py`
2. Call `login_required_json()` first (same as other API routes)
3. Parse JSON body — validate type, title, amount, category (same rules as `create_transaction`)
4. Execute `UPDATE transactions SET type=?, title=?, amount=?, category=?, date=?, notes=? WHERE id=? AND user_id=?`
5. If `rowcount == 0` return 404, else return `{"message": "Transaction updated successfully"}`

**Relevant Context:**
- See `delete_transaction` in [`app.py`](app.py:195) for the ownership check pattern using `WHERE id=? AND user_id=?`
- See `create_transaction` in [`app.py`](app.py:162) for the full validation pattern to replicate
- `login_required_json()` defined at [`app.py`](app.py:69)

**Status:** [ ] pending

---

## Sub-Task 2: Add Edit Button in `dashboard.html`

**Intent:** Add an "Edit" button in each transaction row that opens the edit modal pre-filled with that transaction's data.

**Expected Outcomes:**
- Each row has an edit button next to the existing delete button
- Clicking calls a JS function `openEditModal(tx)` passing the full transaction object
- Button is styled consistently (`.button.ghost` or similar, matching existing delete button area)

**Todo List:**
1. In the `transactions.map(...)` template string in `dashboard.html` (line 43), add a button `<button class="edit-button" onclick="openEditModal(${JSON.stringify(tx).replace(/"/g, '&quot;')})">✎</button>` in the last `<td>` before the delete button

**Relevant Context:**
- See [`dashboard.html`](templates/dashboard.html:43) — the `.map()` row template string, last `<td>` already has the delete button
- `.delete-button` style is in [`static/style.css`](static/style.css:22) — add a matching `.edit-button` style

**Status:** [ ] pending

---

## Sub-Task 3: Build the Edit Modal in `dashboard.html`

**Intent:** Add a hidden modal overlay to the dashboard page. When `openEditModal(tx)` is called, the modal appears with all fields pre-filled from the transaction object. On submit it calls `PUT /api/transactions/<id>`, closes the modal, and refreshes the list.

**Expected Outcomes:**
- Modal appears over the page with a backdrop
- Form fields (type, title, amount, category, date, notes) pre-filled with existing values
- Submit calls `PUT /api/transactions/<id>` with updated values
- On success: modal closes, `loadData()` is called to refresh the list
- On error: inline error message shown inside the modal
- Cancel button closes modal without saving

**Todo List:**
1. Add modal HTML just before the closing `</main>` tag in `dashboard.html` — a `<div id="edit-modal" class="modal-overlay">` containing a `.panel` with the edit form (same field layout as the add form)
2. Add `openEditModal(tx)` JS function — stores `tx.id`, sets each form field value, shows the modal
3. Add `closeEditModal()` JS function — hides the modal, clears error
4. Add form `submit` handler for the edit form — calls `PUT /api/transactions/<id>`, on success calls `closeEditModal()` + `loadData()`
5. Add modal CSS to `static/style.css` — `.modal-overlay` (fixed fullscreen backdrop), centered `.panel` inside it

**Relevant Context:**
- Match the exact field order and CSS classes from the add-form in [`dashboard.html`](templates/dashboard.html:20) — `.form-grid`, `select#tx-type`, `input#tx-amount`, etc.
- Use **new IDs** for edit modal fields (e.g. `edit-type`, `edit-amount`) to avoid conflict with the add form
- The modal `.panel` already has all needed styles from [`static/style.css`](static/style.css:22)
- `loadData()` is already defined in the page JS — reuse it after a successful edit

**Status:** [ ] pending

---

## Sub-Task 4: Add Tests for Edit Transaction

**Intent:** Add pytest test cases that verify the `PUT` API works correctly, including the security check (user cannot edit another user's transaction).

**Expected Outcomes:**
- Editing a valid transaction returns `200` and the change is reflected in `GET /api/transactions`
- Editing a non-existent transaction returns `404`
- Unauthenticated edit attempt returns `401`

**Todo List:**
1. Add `test_edit_transaction` in `test_app.py` — login, create transaction, call `PUT /api/transactions/<id>` with changed title/amount, assert `200`, then `GET` and assert updated values
2. Add `test_edit_transaction_not_found` — login, call `PUT /api/transactions/99999`, assert `404`
3. Add `test_edit_transaction_unauthorized` — no login, call `PUT /api/transactions/1`, assert `401`

**Relevant Context:**
- Follow the pattern in [`test_app.py`](test_app.py:73) (`test_add_and_get_transaction_api`) for create + verify flow
- Use `content_type="application/json"` and `json.dumps(...)` for request body

**Status:** [ ] pending
