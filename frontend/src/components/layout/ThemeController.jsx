import { useEffect } from 'react';
import { useStore } from '../../store/useStore';

const ThemeController = () => {
    const theme = useStore((state) => state.theme);

    useEffect(() => {
        document.body.setAttribute('data-theme', theme);
    }, [theme]);

    return null;
};

export default ThemeController;
