# Introduction

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app). With Electron used on top of it.

## Important Scripts

In the project directory, you can run:

### `npm i`

Install all dependencies of the project. This command is needed before running or it will give errors.

### `npm run dev`

Runs the app in the development mode.

The application will reload if you make edits.\
You will also see any lint errors in the console.

### `npm run make`

Builds the app for production to the `out` folder. This will create an executable for the current operating system.\
It correctly bundles React in production mode and optimizes the build for the best performance.

## First time setup

Due to some configuration changes being in the `node_modules` folder and thus in the gitignore, the following change needs to be made **after** the first `npm i`: 

### Add html-loader to webpack loaders

After running `npm i`, navigate to the `node_modules` folder and find the `react-scripts` folder.\
In there go to `config` and then `webpack.config.js`.

Scroll down to line 578 and paste the following code: 

```javascript
// Adds support for html files
{
    test: /\.html$/,
    use: 'html-loader'
},
```

When these steps are done, start the application with `npm run dev`.