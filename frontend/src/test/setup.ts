import "@testing-library/jest-dom/vitest";

// jsdom には scrollIntoView がないためモック
Element.prototype.scrollIntoView = () => {};
