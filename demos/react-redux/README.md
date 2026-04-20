# react-redux demo

A React 18 + Redux Toolkit app with TypeScript. Manages user authentication state and a product catalog.

## Structure

- `src/store/` — Redux slices and store setup
  - `authSlice.ts` — authentication state (logged out initially)
  - `productsSlice.ts` — async product fetching
  - `index.ts` — store configuration
- `src/api/` — Axios API client (`auth.ts`, `products.ts`)
- `src/components/` — React components
- `src/hooks/` — typed `useAppDispatch` / `useAppSelector`

## Conventions

- All async thunks use `createAsyncThunk` from `@reduxjs/toolkit`
- Slices export actions and selectors together from the same file
- Selectors are named `select*` (e.g. `selectIsAuthenticated`, `selectCurrentUser`)
- Components dispatch via `useAppDispatch`, never `store.dispatch` directly
- Tests use Vitest + `@testing-library/react`
