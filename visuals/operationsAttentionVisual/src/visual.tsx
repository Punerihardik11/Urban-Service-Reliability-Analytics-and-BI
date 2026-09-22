"use strict";

import powerbi from "powerbi-visuals-api";
import React from "react";
import { createRoot, type Root } from "react-dom/client";

import "../style/visual.less";
import "./styles/tailwind.generated.css";

import { OperationsAttention } from "./components/attention/OperationsAttention";

import VisualConstructorOptions =
  powerbi.extensibility.visual.VisualConstructorOptions;

import VisualUpdateOptions =
  powerbi.extensibility.visual.VisualUpdateOptions;

import IVisual =
  powerbi.extensibility.visual.IVisual;

export class Visual implements IVisual {
  private root: Root;

  constructor(options: VisualConstructorOptions) {
    this.root = createRoot(options.element);
  }

  public update(_options: VisualUpdateOptions): void {
    this.root.render(
      <div
        style={{
          width: "100%",
          height: "100%",
          boxSizing: "border-box",
          background: "transparent",
        }}
      >
        <OperationsAttention />
      </div>
    );
  }

  public destroy(): void {
    this.root.unmount();
  }
}