# Frontend

This folder is reserved for the React (TypeScript) frontend implementation.

## Requirements

- **Framework:** Use **React** with **TypeScript**
- **Language:** TypeScript
- **UI Library:** Material UI (MUI)
- **Authentication:** Login must integrate with Django backend  
- **Tooling:** Code must demonstrate use of:
  - React best practices  
  - UI design principles and clean component styling  
  - TypeScript and JavaScript fundamentals  
  - Automated code consistency tooling (e.g. ESLint, Prettier)
  - Unit testing for at least one UI component
- **Bundler:** Vite (preferred)

## ✨ Features to Implement

### 🔐 Login Page
- Authenticates with the Django backend
- All routes after login should be protected

### 📁 My Files Page
- A button to select and upload a document
- Below the button: a paginated data grid showing uploaded files
- Data grid columns:
  - File Name  
  - Version  
  - Actions:
    - **View Versions:** Opens modal listing file versions with copy-to-clipboard shareable links
    - **Download Latest:** Downloads latest version of the file
    - **Upload New Version:** Opens modal showing next version number and allows file upload
    - **Favorite:** Marks file as a favorite (persisted locally); shows in a separate "Favorites" tab

## Notes

- Submissions using frameworks other than React (e.g., Vue, Angular) will not be considered.
