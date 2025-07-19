AttributeError: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).
Traceback:
File "/mount/src/streamlit-extranet/app.py", line 169, in <module>
    main()
    ~~~~^^
File "/mount/src/streamlit-extranet/app.py", line 163, in main
    afficher_calendrier(df)
    ~~~~~~~~~~~~~~~~~~~^^^^
File "/mount/src/streamlit-extranet/app.py", line 107, in afficher_calendrier
    (df["date_arrivee"].dt.month == mois_index) &
     ^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/core/generic.py", line 6318, in __getattr__
    return object.__getattribute__(self, name)
           ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/core/accessor.py", line 224, in __get__
    accessor_obj = self._accessor(obj)
File "/home/adminuser/venv/lib/python3.13/site-packages/pandas/core/indexes/accessors.py", line 643, in __new__
    raise AttributeError("Can only use .dt accessor with datetimelike values")
