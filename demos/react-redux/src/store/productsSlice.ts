import { createAsyncThunk, createSlice } from "@reduxjs/toolkit";

export interface Product {
  id: string;
  name: string;
  priceCents: number;
  category: string;
}

interface ProductsState {
  items: Product[];
  status: "idle" | "loading" | "succeeded" | "failed";
  error: string | null;
}

const initialState: ProductsState = {
  items: [],
  status: "idle",
  error: null,
};

export const fetchProducts = createAsyncThunk("products/fetchAll", async (category: string) => {
  const res = await fetch(`/api/products/${category}/`);
  if (!res.ok) throw new Error("Failed to fetch products");
  return (await res.json()) as Product[];
});

const productsSlice = createSlice({
  name: "products",
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchProducts.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(fetchProducts.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.items = action.payload;
      })
      .addCase(fetchProducts.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.error.message ?? "Unknown error";
      });
  },
});

export default productsSlice.reducer;

export const selectProducts = (state: { products: ProductsState }) => state.products.items;
export const selectProductsStatus = (state: { products: ProductsState }) => state.products.status;
